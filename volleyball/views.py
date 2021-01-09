from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import UpdateView, CreateView
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from .forms import PlayerCreationForm, EventCreateForm, GroupEventCreateForm
from .models import Player, Court, Event, Group, Membership, Participation


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['events'] = Event.objects.get_valid().filter(Q(participants=request.user) | Q(initiator=request.user))
        context['groups'] = Group.objects.filter(members=request.user).exclude(membership__status=Membership.PENDING)
        if len(context['groups']) > 0:
            context['group_events'] = Event.objects.get_valid().filter(group__in=[g.id for g in context['groups']])
    return render(request, 'volleyball/index.html', context=context)


class PlayerCreateView(CreateView):
    model = Player
    form_class = PlayerCreationForm
    template_name = 'volleyball/register.html'
    success_url = reverse_lazy('login')


class PlayerUpdateView(LoginRequiredMixin, UpdateView):
    model = Player
    fields = ['first_name', 'last_name', 'date_of_birth', 'mobile_number']
    template_name = 'volleyball/settings.html'
    success_url = reverse_lazy('setting')

    def get_object(self, queryset=None):
        return self.request.user


class CourtListView(generic.ListView):
    model = Court
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        courts = cache.get('courts')
        if courts is None:
            courts = Court.objects.all()
            cache.set('courts', courts)
        return courts


class CourtCreateView(LoginRequiredMixin, generic.CreateView):
    model = Court
    fields = '__all__'


class CourtDetailView(generic.DetailView):
    model = Court


class GroupListView(generic.ListView):
    model = Group
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        groups = cache.get('groups')
        if groups is None:
            groups = Group.objects.all()
            cache.set('groups', groups)
        return groups


class GroupDetailView(generic.DetailView):
    queryset = Group.objects.select_related('organizer').select_related('court').prefetch_related(
        Prefetch('members', queryset=Membership.objects.select_related('player'))
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.get_valid().filter(group=self.object)

        memberships = self.object.members.all()
        context['memberships_pending'] = [m for m in memberships if m.status == Membership.PENDING]
        context['memberships_member'] = [m for m in memberships if m.status == Membership.MEMBER]
        context['memberships_admin'] = [m for m in memberships if m.status == Membership.ADMIN]

        status = next((m.status for m in memberships if m.player == self.request.user), None)
        if status != None:
            is_XXX = {
                Membership.ORGANIZER: 'is_organizer',
                Membership.ADMIN: 'is_admin',
                Membership.MEMBER: 'is_member',
                Membership.PENDING: 'is_pending',
            }[status]
            context[is_XXX] = True

        return context


class GroupCreateView(LoginRequiredMixin, generic.CreateView):
    model = Group
    fields = ['name', 'court', 'about']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method'] = _('Create')
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.organizer = self.request.user
                self.object.save()
                self.object.members.add(self.request.user, through_defaults={'status': Membership.ORGANIZER})
        except:
            return HttpResponseForbidden()
        return HttpResponseRedirect(self.get_success_url())


class GroupUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Group
    fields = ['about']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method'] = _('Edit')
        return context

    def post(self, request, *args, **kwargs):
        if self.get_object().organizer != self.request.user:
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.organizer = self.request.user
                self.object.save()
                self.object.members.add(self.request.user, through_defaults={'status': Membership.ORGANIZER})
        except:
            return HttpResponseForbidden()
        return HttpResponseRedirect(self.get_success_url())


class GroupDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Group
    success_url = reverse_lazy('group-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.organizer != self.request.user:
            return HttpResponseForbidden()
        self.object.delete()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


@login_required
def group_join(request, pk):
    group = get_object_or_404(Group, pk=pk)
    membership = Membership.objects.create(player=request.user, group=group, status=Membership.PENDING)
    membership.save()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[pk]))


@login_required
def group_quit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if group.organizer == request.user:
        return HttpResponseForbidden()
    group.members.remove(request.user)
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[pk]))


class GroupEventCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = GroupEventCreateForm
    template_name = 'volleyball/group_event_form.html'

    def get_initial(self):
        group = get_object_or_404(Group, pk=self.kwargs['pk'])
        return {
            'public': False,
            'court': group.court,
        }

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)
            self.object.initiator = self.request.user
            group = get_object_or_404(Group, pk=self.kwargs['pk'])
            membership = Membership.objects.get(group=group, player=self.request.user)
            assert membership.is_member
            self.object.group = group
            self.object.save()
            return HttpResponseRedirect(self.get_success_url())
        except:
            return HttpResponseForbidden()


@login_required
def membership_delete(request, pk):
    target_membership = get_object_or_404(Membership, pk=pk)
    origin_status = target_membership.status
    user_membership = get_object_or_404(Membership, group=target_membership.group, player=request.user)
    if any([
        origin_status in [Membership.PENDING, Membership.MEMBER] and not user_membership.is_admin,
        origin_status in [Membership.ADMIN] and not user_membership.is_organizer,
        origin_status in [Membership.ORGANIZER],
    ]): return HttpResponseForbidden()

    target_membership.delete()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[target_membership.group_id]))


@login_required
def membership_to_member(request, pk):
    target_membership = get_object_or_404(Membership, pk=pk)
    origin_status = target_membership.status
    user_membership = get_object_or_404(Membership, group=target_membership.group, player=request.user)
    if any([
        origin_status in [Membership.PENDING] and not user_membership.is_admin,
        origin_status in [Membership.ADMIN] and not user_membership.is_organizer,
        origin_status in [Membership.ORGANIZER],
    ]): return HttpResponseForbidden()

    target_membership.status = Membership.MEMBER
    target_membership.save()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[target_membership.group_id]))


@login_required
def membership_to_admin(request, pk):
    target_membership = get_object_or_404(Membership, pk=pk)
    origin_status = target_membership.status
    user_membership = get_object_or_404(Membership, group=target_membership.group, player=request.user)
    if any([
        origin_status in [Membership.ORGANIZER],
        not user_membership.is_organizer,
    ]): return HttpResponseForbidden()

    target_membership.status = Membership.ADMIN
    target_membership.save()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[target_membership.group_id]))


class EventListView(generic.ListView):
    queryset = Event.objects.get_valid().get_public()
    paginate_by = settings.PAGINATE_BY


class EventDetailView(generic.DetailView):
    queryset = Event.objects.select_related('initiator').select_related('court').prefetch_related('participants')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_viewable_by(request.user):
            return HttpResponseForbidden()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.object.can_edit_by(self.request.user)
        return context


class EventCreateView(LoginRequiredMixin, generic.CreateView):
    model = Event
    form_class = EventCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method'] = _('Create')
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.initiator = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class EventUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Event
    fields = ['court_detail', 'player_quota', 'play_detail']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method'] = _('Edit')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_edit_by(request.user):
            return HttpResponseForbidden()
        return super().post(request, *args, **kwargs)


class EventDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Event
    success_url = reverse_lazy('event-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if any([
            self.object.initiator != self.request.user,
            self.object.play_date < datetime.today().date(),
        ]): return HttpResponseForbidden()

        self.object.delete()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


@login_required
def event_signup(request, pk):
    event = get_object_or_404(Event.objects.get_valid(), pk=pk)
    participants = list(Participation.objects.filter(event=event))
    if any([
        not event.is_viewable_by(request.user),
        len(participants) == event.player_quota,
    ]): return HttpResponseForbidden()
    if request.user not in participants:
        event.participants.add(request.user)
    return HttpResponseRedirect(reverse_lazy('event-detail', args=[pk]))


@login_required
def event_quit(request, pk):
    event = get_object_or_404(Event.objects.get_valid(), pk=pk)
    if request.user in event.participants.all():
        event.participants.remove(request.user)
    return HttpResponseRedirect(reverse_lazy('event-detail', args=[pk]))

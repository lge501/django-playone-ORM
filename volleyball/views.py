from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import UpdateView, CreateView

from .forms import PlayerCreationForm, EventCreateForm
from .models import Player, Court, Event, Group, Membership, Participation


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['groups'] = Group.objects.filter(members=request.user)
        context['events'] = list(Event.objects.filter(Q(participants=request.user) | Q(initiator=request.user)))
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


class CourtCreateView(LoginRequiredMixin, generic.CreateView):
    model = Court
    fields = '__all__'


class CourtDetailView(generic.DetailView):
    model = Court


class GroupListView(generic.ListView):
    model = Group


class GroupDetailView(generic.DetailView):
    queryset = Group.objects.select_related('organizer').select_related('court').prefetch_related(
        Prefetch('members', queryset=Membership.objects.select_related('player'))
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.organizer = self.request.user
                self.object.save()
                self.object.members.add(self.request.user, through_defaults={'status': Membership.ORGANIZER})
        except:
            return HttpResponse(status=403)
        return HttpResponseRedirect(self.get_success_url())


class GroupUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Group
    fields = ['about']


class GroupDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Group
    success_url = reverse_lazy('group-list')

    def get(self, request, *args, **kwargs):
        if self.get_object().organizer != self.request.user:
            return HttpResponse(status=403)
        return super().get(request, *args, **kwargs)


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
        return HttpResponse(status=403)
    group.members.remove(request.user)
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[pk]))


@login_required
def membership_delete(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    user_status = get_object_or_404(Membership, group=membership.group, player=request.user).status
    if membership.status in [Membership.PENDING, Membership.MEMBER]:
        if user_status not in [Membership.ORGANIZER, Membership.ADMIN]:
            return HttpResponse(status=403)
    elif membership.status == Membership.ADMIN:
        if user_status != Membership.ORGANIZER:
            return HttpResponse(status=403)
    elif membership.status == Membership.ORGANIZER:
        return HttpResponse(status=403)

    membership.delete()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[membership.group_id]))


@login_required
def membership_to_member(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    user_status = get_object_or_404(Membership, group=membership.group, player=request.user).status
    if membership.status == Membership.PENDING:
        if user_status not in [Membership.ORGANIZER, Membership.ADMIN]:
            return HttpResponse(status=403)
    if membership.status == Membership.ADMIN:
        if user_status != Membership.ORGANIZER:
            return HttpResponse(status=403)
    if membership.status == Membership.ORGANIZER:
        return HttpResponse(status=403)

    membership.status = Membership.MEMBER
    membership.save()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[membership.group_id]))


@login_required
def membership_to_admin(request, pk):
    membership = get_object_or_404(Membership, pk=pk)
    user_status = get_object_or_404(Membership, group=membership.group, player=request.user).status
    if user_status != Membership.ORGANIZER:
        return HttpResponse(status=403)
    membership.status = Membership.ADMIN
    membership.save()
    return HttpResponseRedirect(reverse_lazy('group-detail', args=[membership.group_id]))


class EventListView(generic.ListView):
    queryset = Event.objects.filter(play_date__gt=datetime.now())


class EventDetailView(generic.DetailView):
    queryset = Event.objects.select_related('initiator').select_related('court').prefetch_related('participants')


class EventCreateView(LoginRequiredMixin, generic.CreateView):
    model = Event
    form_class = EventCreateForm
    # fields = ['court', 'court_detail', 'play_date', 'play_start_time', 'player_quota', 'play_detail']

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.initiator = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class EventUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Event
    fields = ['court_detail', 'player_quota', 'play_detail']


class EventDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Event
    success_url = reverse_lazy('event-list')


@login_required
def event_signup(request, pk):
    event = get_object_or_404(Event, pk=pk)
    participants = list(Participation.objects.filter(event=event))
    if len(participants) == event.player_quota:
        return HttpResponse(status=403)
    if request.user not in participants:
        event.participants.add(request.user)
    return HttpResponseRedirect(reverse_lazy('event-detail', args=[pk]))


@login_required
def event_quit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.user in event.participants.all():
        event.participants.remove(request.user)
    return HttpResponseRedirect(reverse_lazy('event-detail', args=[pk]))

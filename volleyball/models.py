from django.conf import settings
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.core import validators
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.urls import reverse

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from django.utils.translation import gettext_lazy as _


class PlayerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            last_login=now,
            date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(
            email,
            password=password,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Player(AbstractBaseUser):
    MALE = 1
    FEMALE = 2
    GENDER_CHOICES = [
        # (0, 'Not known'),
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        # (9, 'Not applicable'),
    ]

    email = models.EmailField(_('email'), max_length=255, unique=True)
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    gender = models.PositiveSmallIntegerField(_('gender'), choices=GENDER_CHOICES)
    date_of_birth = models.DateField(_('date of birth'), null=True)
    mobile_number = models.CharField(_('mobile number'), max_length=30, blank=True,
                                     help_text=_('digits and +-() only.'),
                                     validators=[validators.RegexValidator(r'^[0-9+()-]+$',
                                                                           _('Enter a valid mobile number.'),
                                                                           'invalid')])
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = PlayerManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'gender', 'date_of_birth']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True


@receiver(user_signed_up)
def signup_facebook_extra_fields(sociallogin, user, **kwargs):
    if sociallogin.account.provider == 'facebook':
        # user_data = user.socialaccount_set.filter(provider='facebook')[0].extra_data
        # picture_url = "http://graph.facebook.com/" + sociallogin.account.uid + "/picture?type=large"
        gender = sociallogin.account.extra_data['gender']
        birthday = sociallogin.account.extra_data['birthday']
        user.gender = Player.MALE if gender == 'male' else Player.FEMALE
        user.date_of_birth = datetime.strptime(birthday, '%m/%d/%Y')
        user.save()


class Court(models.Model):
    name = models.CharField(_('name'), max_length=80, unique=True)
    photo = models.ImageField(_('photo'), upload_to='images/', null=True, blank=True)

    # CITY_CHOICES = [
    #     (1, 'Male'),
    #     (2, 'Female'),
    # ]
    # city = models.PositiveSmallIntegerField(_('city'), choices=CITY_CHOICES, default=1)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('court-detail', args=[str(self.id)])


class Group(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    organizer = models.ForeignKey(Player, verbose_name='organizer', on_delete=models.CASCADE, related_name='+')
    court = models.ForeignKey(Court, verbose_name='court', on_delete=models.CASCADE)
    about = models.TextField(_('about'), max_length=600, blank=True)
    members = models.ManyToManyField(Player, through='Membership')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group-detail', args=[str(self.id)])


class Membership(models.Model):
    ORGANIZER = 0
    ADMIN = 1
    MEMBER = 2
    PENDING = 3
    STATUS_CHOICES = [
        (ORGANIZER, 'organizer'),
        (ADMIN, 'admin'),
        (MEMBER, 'member'),
        (PENDING, 'pending'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(_('status'), choices=STATUS_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'player'], name='unique_membership')
        ]

    @property
    def is_member(self):
        return self.status in [self.ORGANIZER, self.ADMIN, self.MEMBER]

    @property
    def is_admin(self):
        return self.status in [self.ORGANIZER, self.ADMIN]

    @property
    def is_organizer(self):
        return self.status == self.ORGANIZER


class EventQuerySet(models.QuerySet):
    def get_public(self):
        return self.filter(is_public=True)

    def get_valid(self):
        return self.filter(is_expired=False)


class EventManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('group', 'court')


class Event(models.Model):
    NET_TYPE_CHOICES = [
        (0, 'Middle'),
        (1, 'Male'),
        (2, 'Female'),
    ]
    initiator = models.ForeignKey(Player, verbose_name=_('initiator'), on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('group'), on_delete=models.CASCADE, null=True)
    is_public = models.BooleanField(_('is public'), default=True)
    court = models.ForeignKey(Court, verbose_name=_('court'), on_delete=models.CASCADE)
    court_detail = models.TextField(_('court detail'), max_length=300, blank=True)
    play_date = models.DateField(_('play date'))
    play_start_time = models.TimeField(_('play start time'), )
    # play_end_time = models.TimeField(_('play end time'), )
    is_expired = models.BooleanField(_('is expired'), default=False)
    player_quota = models.PositiveSmallIntegerField(_('player quota'), blank=False, default=6)
    play_detail = models.TextField(_('play detail'), max_length=300, blank=True)
    participants = models.ManyToManyField(Player, through='Participation', related_name='participations')
    # net_type = models.PositiveSmallIntegerField(_('net type'), choices=NET_TYPE_CHOICES, default=1)

    objects = EventManager.from_queryset(EventQuerySet)()

    class Meta:
        ordering = ['play_date', 'play_start_time']

    def __str__(self):
        return '{} {} {}'.format(self.play_date.strftime(settings.DATE_FORMAT), self.play_start_time.strftime(settings.TIME_FORMAT), self.court.name)

    def get_absolute_url(self):
        return reverse('event-detail', args=[str(self.id)])

    def get_group_membership(self, user):
        try:
            return Membership.objects.get(group=self.group, player=user)
        except:
            return None

    def has_group_member(self, user):
        # try:
        #     membership = Membership.objects.get(group=self.group, player=user)
        #     return membership.is_admin()
        # except Membership.DoesNotExist:
        #     return False
        membership = self.get_group_membership(user)
        if membership:
            return membership.is_member
        else:
            return False

    def has_group_admin(self, user):
        membership = self.get_group_membership(user)
        if membership:
            return membership.is_admin
        else:
            return False

    def is_viewable_by(self, user):
        return self.is_public or self.initiator == user or self.has_group_member(user)

    def can_edit_by(self, user):
        return not self.is_expired and user.is_authenticated and (self.initiator == user or self.has_group_admin(user))


class Participation(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['event', 'player'], name='unique_participation')
        ]

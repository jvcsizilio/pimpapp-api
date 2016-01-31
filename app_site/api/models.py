# TODO

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class CarroceiroAlreadyExistsException(Exception):
    pass

class Carroceiro(models.Model):
    """
    Class used for modeling a instance of Carroceiro in our DB.
    by default, this table will be addressed as carroceiro_carroceiro
    """

    CATADOR = 'C'
    COOPERATIVA = 'O'
    ECOPONTO = 'P'

    TYPE_CHOICES = (
        (CATADOR, 'Catador'),
        (COOPERATIVA, 'Cooperativa'),
        (ECOPONTO, 'Ecoponto'),
    )

    name = models.CharField(max_length=120, default='')
    phone = models.CharField(max_length=15,
        validators=[RegexValidator(regex=r'^\d{8,15}$',
        message='Phone number must have at least 8 digits and/or up to 15 digits.')],
        default='', null=True, blank=True)

    type = models.CharField(max_length=1, default=CATADOR,
           choices=TYPE_CHOICES)

    @property
    def geolocation(self):
        obj = self.latitudelongitude_set.all().latest('created_on')
        return obj

    @property
    def materials(self):
        obj = self.materials_set.all().latest('created_on')
        return obj

    @property
    def profile_info(self):
        # TODO: filter
        obj = self.profileinfo_set.objects.all().latest('created_on')
        return obj

    def __str__(self):
        return self.name


class Authorship(models.Model):
    """
        DOCS: TODO
    """
    APPROVED = 'A'
    REJECTED = 'R'
    PENDING = 'P'

    MODERATION_CHOICES = (
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (PENDING, 'Pending'),
    )

    class Meta:
        abstract = True

    user = models.ForeignKey(User, unique=False, blank=False)
    carroceiro = models.ForeignKey(Carroceiro, unique=False, blank=False)
    created_on =  models.DateTimeField(auto_now_add=True)
    moderation_status = models.CharField(max_length=1,
                                      choices=MODERATION_CHOICES,
                                      default=PENDING)

class Materials(Authorship):
    # TODO: Write the rest
    paper = models.BooleanField(default=False)
    freight = models.BooleanField(default=False)
    large_objects = models.BooleanField(default=False)


class LatitudeLongitude(Authorship):
    """
        DOCS: TODO
    """
    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)
    # Reference point
    address = models.CharField(max_length=120, default='', null=True, blank=True)


class Rating(Authorship):
    """
        DOCS: TODO
    """
    rating = models.IntegerField(blank=True)
    comment = models.CharField(max_length=140, blank=True)

    def clean(self):
        if not self.rating and not self.comment:
            raise ValidationError(_('Rating or comment required.'))


class Photo(Authorship):
    # file will be uploaded to MEDIA_ROOT/full_photo
    full_photo = models.ImageField(upload_to='full_photo')
    thumbnail = models.ImageField(blank=True, upload_to='thumbnail')


class BaseProfileInfo(Authorship):
    """
        DOCS: TODO
    """
    VIVO = 'V'
    TIM = 'T'
    CLARO = 'C'
    OI = 'O'
    NEXTEL = 'N'
    # Algar
    # Sercomtel
    # Porto Seguro

    # Mobile Network Operator (MNO)
    MNO_CHOICES = (
        (VIVO, 'Vivo'),
        (TIM, 'TIM'),
        (CLARO, 'Claro'),
        (OI, 'Oi'),
        (NEXTEL, 'Nextel'),
    )

    class Meta:
        abstract = True

    name = models.CharField(max_length=64)

    phone = models.CharField(max_length=16)
    mno = models.CharField(max_length=11,
        verbose_name=u"Operadora Móvel")
    has_whatsapp = models.BooleanField(default=False)

    address = models.CharField(max_length=128,
        verbose_name=u"Endereço onde costuma trabalhar.")
    region = models.CharField(max_length=64,
        verbose_name=u"Região onde costuma trabalhar.") # Makes sense?
    city = models.CharField(max_length=64,
        verbose_name=u"Cidade em que trabalha")

    has_motor_vehicle = models.BooleanField(default=False)
    carroca_pimpada = models.BooleanField(default=False)


class ProfileInfo(BaseProfileInfo):
    """
        DOCS: TODO
    """
    def save(self, *args, **kwargs):
        super(ProfileInfo, self).save(*args, **kwargs)
        self.archive()

    def archive(self):
        obj = ProfileInfoHistoric.from_profile(self)
        obj.save()


class ProfileInfoHistoric(BaseProfileInfo):
    """
        DOCS: TODO
    """
    original_pk = models.IntegerField()

    @classmethod
    def from_profile(cls, profile_info, save=False):

        self = cls()

        fields = ['name', 'phone', 'mno',
            'has_whatsapp', 'address', 'region',
            'city', 'has_motor_vehicle', 'carroca_pimpada']

        self.original_pk = profile_info.pk

        for field in fields:
            value = getattr(profile_info, field)
            setattr(self, field, value)

        if save:
            self.save()

        return self

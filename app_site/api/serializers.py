from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Rating
from .models import Photo
from .models import Phone
from .models import Carroceiro
from .models import Material
from .models import LatitudeLongitude
from .models import Collect
from .models import Residue
from .models import ResiduePhoto
from .models import ResidueLocation


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ('carroceiro', 'created_on',
                  'freight', 'large_objects', 'demolition_waste',
                  'e_waste', 'paper', 'glass', 'plastic', 'metal',
                  'wood', 'cooking_oil')


class LatitudeLongitudeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatitudeLongitude
        fields = ('carroceiro', 'created_on',
                  'latitude', 'longitude', 'reverse_geocoding')


class PhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phone
        fields = ('pk', 'carroceiro', 'phone', 'mno', 'has_whatsapp', 'mobile_internet', 'notes')


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('pk', 'user', 'carroceiro', 'created_on',
                  'rating', 'comment')


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ('pk', 'carroceiro', 'created_on',
                  'full_photo', 'thumbnail')


class CarroceiroSerializer(serializers.ModelSerializer):

    class Meta:
        model = Carroceiro
        fields = ('pk', 'catador_type', 'geolocation', 'phones',
                'name', 'address_base', 'region', 'city',
                'country', 'has_motor_vehicle', 'carroca_pimpada',
                'is_locked')

    geolocation = LatitudeLongitudeSerializer(required=False)
    phones = PhoneSerializer(required=False, many=True)
    #materials = MaterialSerializer(required=False)


class CollectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collect
        fields = ('pk', 'catador_confirms', 'user_confirms', 'active',
                  'author', 'carroceiro', 'geolocation', 'photo_collect_user')


class ResiduePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResiduePhoto
        fields = ['full_photo', ]


class ResidueSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Residue
        fields = '__all__'

    def get_photos(self, obj):
        return ResiduePhotoSerializer(obj.residue_photos, many=True).data

    def get_latitude(self, obj):
        try:
            return obj.residuelocation.latitude
        except:
            return None

    def get_longitude(self, obj):
        try:
            return obj.residuelocation.longitude
        except:
            return None


class ResidueLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResidueLocation
        fields = '__all__'

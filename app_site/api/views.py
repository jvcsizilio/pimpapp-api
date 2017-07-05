from rest_framework import serializers
from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, \
    IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import detail_route
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, HttpResponse
from base64 import b64decode
from django.core.files.base import ContentFile
import uuid

from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .models import ModeratedModel
from .models import Catador
from .models import LatitudeLongitude
from .models import MobileCatador
from .models import Rating
from .models import Collect
from .models import Residue
from .models import Cooperative
from .models import GeorefCatador
from .models import Mobile
from .models import PhotoResidue
from .models import Material
from .models import GeorefResidue
from .models import PhotoCollectCatador
from .models import PhotoCollectUser
from .models import RatingCatador
from .models import RatingCooperative

from .serializers import RatingSerializer
from .serializers import MobileSerializer
from .serializers import CatadorSerializer
from .serializers import MaterialSerializer
from .serializers import CollectSerializer
from .serializers import UserSerializer
from .serializers import ResidueSerializer
from .serializers import CooperativeSerializer
from .serializers import LatitudeLongitudeSerializer
from .serializers import PhotoResidueSerializer
from .serializers import PhotoCollectCatadorSerializer
from .serializers import PhotoCollectUserSerializer
from .serializers import CatadorsPositionsSerializer
from .serializers import PasswordSerializer

from .permissions import IsObjectOwner

from .pagination import PostLimitOffSetPagination

public_status = (ModeratedModel.APPROVED, ModeratedModel.PENDING)


class PermissionBase(APIView):
    def get_permissions(self):
        if self.request.method in ['GET', 'OPTIONS', 'HEAD', 'POST']:
            self.permission_classes = [IsAuthenticated]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsObjectOwner]

        return super(PermissionBase, self).get_permissions()


class RecoBaseView(PermissionBase):
    pagination_class = PostLimitOffSetPagination


class UserViewSet(viewsets.ModelViewSet):
    '''
        Endpoint used to create, update and retrieve users
        Allow: GET, POST, UPDATE, OPTIONS
    '''
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'update', 'options']


@detail_route(methods=['post'])
def set_password(self, request, pk=None):
    """
    Set a users password via thew api
    :param request:
    :param pk:
    :return:
    """

    user = self.get_object()
    serializer = PasswordSerializer(data=request.data)
    if serializer.is_valid():
        if user.check_password(serializer.data['old_password']):
            user.set_password(serializer.data['password'])
            user.save()
            return Response({'content_type': 'Password set'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'content_type': 'Current password incorrect'},
                            status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


def create_new_comment(data):
    comment = Rating(comment=data['comment'], author_id=data['author'],
                     rating=data['rating'],
                     carroceiro_id=data['carroceiro'])
    return comment.save()


class CatadorViewSet(viewsets.ModelViewSet):
    """
        CatadorViewSet Routes:

        /api/catadores/
        /api/catadores/<pk>
        /api/catadores/<pk>/comments (GET, POST, PUT, PATCH, DELETE) pass
        pk parameter
        /api/catadores/<pk>/georef (GET, POST)
        /api/catadores/<pk>/phones (GET, POST, DELETE)

    """

    serializer_class = CatadorSerializer
    permission_classes = (IsObjectOwner,)
    queryset = Catador.objects.all()
    http_method_names = ['get', 'post', 'update', 'options', 'patch', 'delete']

    @detail_route(methods=['GET', 'POST'],
                  permission_classes=[IsObjectOwner])
    def georef(self, request, pk=None):
        """
        Get all geolocation from one Catador
        :param request:
        :param pk:
        :return:
        """
        if request.method == 'POST':
            data = request.data

            georeference = LatitudeLongitude.objects.create(
                latitude=data.get('latitude'),
                longitude=data.get('longitude'))

            GeorefCatador.objects.create(
                georef=georeference, catador=self.get_object())

        serializer = LatitudeLongitudeSerializer(
            self.get_object().geolocation, many=True)

        return Response(serializer.data)

    @detail_route(methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
                  permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        catador = self.get_object()

        data = request.data

        if request.method in ['POST']:
            rating = Rating.objects.create(
                comment=data.get('comment'), author=request.user,
                rating=data.get('rating'))

            RatingCatador.objects.create(catador=catador, rating=rating)

        if request.method == 'DELETE':
            rating = get_object_or_404(
                Rating, pk=data.get('pk'), author_id=request.user)
            rating.delete()

        serializer = RatingSerializer(catador.comments, many=True)
        return Response(serializer.data)

    @detail_route(methods=['GET', 'POST', 'PUT', 'DELETE'])
    def phones(self, request, pk=None):
        catador = self.get_object()
        data = request.query_params

        if request.method == 'POST':
            m = Mobile.objects.create(
                phone=data.get('phone'), mno=data.get('mno'),
                has_whatsapp=data.get('has_whatsapp', False),
                mobile_internet=data.get('mobile_internet', False),
                notes=data.get('notes')
            )
            MobileCatador.objects.create(mobile=m, catador=catador)
        elif request.method == 'DELETE':
            Mobile.objects.get(id=data.get('id')).delete()

        serializer = MobileSerializer(catador.phones, many=True)

        return Response(serializer.data)

    @detail_route(methods=['get'])
    def materials(self, request, pk=None):
        catador = self.get_object()
        serializer = MaterialSerializer(catador.materials)
        return Response(serializer.data)


# Analise and see if we have to keep this view
class RatingViewSet(viewsets.ModelViewSet):
    """
        DOCS: TODO
    """
    serializer_class = RatingSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Rating.objects.filter(
        moderation_status__in=public_status)
    pagination_class = PostLimitOffSetPagination


# Analise and see if we have to keep this view
class RatingByCarroceiroViewSet(RecoBaseView, viewsets.ModelViewSet):
    """
        DOCS: TODO
    """
    serializer_class = RatingSerializer

    def get_queryset(self):
        catador = self.kwargs['catador']
        queryset = Rating.objects.filter(
            moderation_status__in=public_status,
            carroceiro__id=Catador(user=self.request.user))


class CollectViewSet(viewsets.ModelViewSet):
    """
        DOCS: TODO
        api/accept_collet/ (POST, GET)
        api/photo_catador/ (POST, GET)
        api/photo_user/ (POST, GET)
    """
    serializer_class = CollectSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Collect.objects.filter()
    http_method_names = ['get', 'options', 'post']

    @detail_route(methods=['POST'])
    def accept_collect(self, request, pk):
        collect = self.get_object()
        catador = Catador.objects.get(user=request.user)
        collect.catador = catador
        collect.save()
        return HttpResponse()

    @detail_route(methods=['POST'])
    def catador_confirms(self, request, pk):
        collect = self.get_object()

        'TODO: MOVER REGRA DE NEGOCIO PARA O MODEL'
        if collect.catador.user != request.user:
            raise serializers.ValidationError(
                'Apenas o catador da coleta pode confirmar.')

        collect.catador_confirms = True
        collect.save()
        return HttpResponse()

    @detail_route(methods=['POST'])
    def user_confirms(self, request, pk):
        collect = self.get_object()

        'TODO: MOVER REGRA DE NEGOCIO PARA O MODEL'
        if collect.residue.user != request.user:
            raise serializers.ValidationError(
                'Apenas o usuário que abriu a coleta pode confirmar.')

        collect.user_confirms = True
        collect.save()
        return HttpResponse()

    @detail_route(methods=['GET', 'POST'])
    def photos_catador(self, request, pk=None):
        """
        Get all PHOTOS from one Collect, and enables the catador
        to upload photos to the collect in question
        """

        collect = self.get_object()

        if request.method == 'POST':
            data = request.data
            photo = request.FILES['full_photo']

            PhotoCollectCatador.objects.create(
                author=request.user, coleta=collect, full_photo=photo)

        serializer = PhotoCollectCatadorSerializer(
            collect.photo_collect_catador, many=True)

        return Response(serializer.data)

    @detail_route(methods=['GET', 'POST'])
    def photos_user(self, request, pk=None):
        """
        Get all PHOTOS from one Collect, and enables the user to upload photos
        to the collect in question
        """

        collect = self.get_object()

        if request.method == 'POST':
            data = request.data
            photo = request.FILES['full_photo']

            PhotoCollectUser.objects.create(
                author=request.user, coleta=collect, full_photo=photo)

        serializer = PhotoCollectUserSerializer(collect.photo_collect_catador,
                                                many=True)

        return Response(serializer.data)


class ResidueViewSet(RecoBaseView, viewsets.ModelViewSet):
    """
        Endpoint used to create, update and retrieve residues
        Allow: GET, POST, UPDATE, OPTIONS

        /api/residues/
        /api/residues/<pk>/
        /api/residues/<pk>/photos/
        /api/residues/<pk>/georef/
    """
    serializer_class = ResidueSerializer
    queryset = Residue.objects.filter()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['id', 'description', 'user']
    http_method_names = ['get', 'post', 'update', 'options', 'patch']

    @detail_route(methods=['GET', 'POST'],
                  permission_classes=[IsObjectOwner])
    def photos(self, request, pk=None):
        """
        Get all PHOTOS from one Residue, and enables to upload photos
        to the residue in question
        """
        residue = self.get_object()

        if request.method == 'POST':
            if request.FILES.get('full_photo'):
                photo = request.FILES['full_photo']
            else:
                photo = b64decode(request.data['full_photo'])
                name = str(uuid.uuid4()) + '.jpg'
                photo = ContentFile(photo, name)

            PhotoResidue.objects.create(
                author=request.user, residue=residue, full_photo=photo)

        serializer = PhotoResidueSerializer(residue.residue_photos, many=True)

        return Response(serializer.data)

    @detail_route(methods=['GET', 'POST', 'UPDATE'],
                  permission_classes=[IsObjectOwner])
    def georef(self, request, pk):
        if request.method == 'POST':
            data = request.data

            georeference = LatitudeLongitude.objects.create(
                latitude=data.get('latitude'),
                longitude=data.get('longitude'))

            GeorefResidue.objects.create(
                georef=georeference, residue=self.get_object())

        serializer = LatitudeLongitudeSerializer(
            self.get_object().residue_location)

        return Response(serializer.data)


class CooperativeViewSet(RecoBaseView, viewsets.ModelViewSet):
    serializer_class = CooperativeSerializer
    queryset = Cooperative.objects.all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'email', 'id']
    ordering_fields = ['name', 'email', 'id']
    http_method_names = ['get', 'post', 'update', 'patch', 'options', 'delete']

    @detail_route(methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
                  permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        cooperative = self.get_object()

        data = request.data

        if request.method in ['POST']:
            rating = Rating.objects.create(
                comment=data.get('comment'), author=request.user,
                rating=data.get('rating'))

            RatingCooperative.objects.create(catador=cooperative, rating=rating)

        if request.method == 'DELETE':
            rating = get_object_or_404(
                Rating, pk=data.get('pk'), author_id=request.user)
            rating.delete()

        serializer = RatingSerializer(cooperative.comments, many=True)
        return Response(serializer.data)


class MaterialsViewSet(RecoBaseView, viewsets.ModelViewSet):
    serializer_class = MaterialSerializer
    queryset = Material.objects.all()
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'id']
    ordering_fields = ['name', 'id']
    http_method_names = ['get', 'options']


class NearestCatadoresViewSet(viewsets.ModelViewSet):
    serializer_class = CatadorsPositionsSerializer
    queryset = Catador.objects.all()


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(
            request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key, 'id': token.user_id})
import time
import uuid
import json
import boto3
from PIL            import Image
from urllib.request import urlopen

from django.views     import View
from django.db.models import (
    Prefetch,
    Q,
    F
)
from django.http      import (
    JsonResponse,
    HttpResponse
)

from .models        import (
    HashTag,
    Photo
)
from account.models import (
    User,
    Collection
)
from auth           import login_check

from photo.tasks import upload_image
from auth import login_check
from my_settings import (
    S3_URL,
    AWS_S3
)
class RelatedPhotoView(View):
    PHOTO_LIMIT = 20

    @login_check
    def get(self, request, user_id, photo_id):
        try:
            photo = Photo.objects.get(id=photo_id)
            photo.views = F('views') +1
            photo.save()

            related_tags = list(HashTag.objects.filter(photo__id = photo_id).values_list('name', flat=True))
            photos = Photo.objects.filter(hashtag__name__in = related_tags).exclude(id=photo_id).prefetch_related(
                "user",
                "collection",
                "photocollection_set",
                "like_set"
            ).distinct()

            result = [{
                "id"                 : photo.id,
                "image"              : photo.image,
                "location"           : photo.location,
                "user_first_name"    : photo.user.first_name,
                "user_last_name"     : photo.user.last_name,
                "user_name"          : photo.user.user_name,
                "user_profile_image" : photo.user.profile_image,
                "user_like"          : photo.like_set.filter(user_id = user_id, status=True).exists(),
                "user_collection"    : photo.photocollection_set.filter(
                    collection = Collection.objects.filter(
                        user_id = user_id,
                        photo = photo
                    ).first()).exists()
            } for photo in photos[:self.PHOTO_LIMIT]]

            return JsonResponse({"tags" : related_tags, "data" : result}, status=200)
        except Photo.DoesNotExist:
            return JsonResponse({'message' : 'NON_EXISTING_PHOTO'}, status=401)
        except ValueError:
            return JsonResponse({"message" : "INVALID_PHOTO"}, status=400)

class RelatedCollectionView(View):
    LIMIT_NUM = 3

    def get(self, request):
        try:
            photo_id = request.GET.get('photo', None)
            user_name = request.GET.get('user', None)
            query = Q()
            if photo_id:
                if Photo.objects.filter(id=photo_id).exists():
                    query &= Q(photocollection__photo__id = int(photo_id))
                else:
                    return JsonResponse({'message' : "NON_EXISTING_PHOTO"}, status=401)
            elif user_name:
                if User.objects.filter(user_name=user_name):
                    query &= Q(user__user_name = user_name)
                else:
                    return JsonResponse({'message' : "NON_EXISTING_USER"}, status=401)

            collections = Collection.objects.filter(query).exclude(
                user__user_name = 'weplash'
            ).prefetch_related(
                Prefetch("photo_set"),
                Prefetch("photo_set__hashtag")
            )

            if photo_id:
                collections = collections[:self.LIMIT_NUM]

            result = [{
                "id"              : collection.id,
                "image"           : [photo.image for photo in collection.photo_set.all()[:self.LIMIT_NUM]],
                "name"            : collection.name,
                "photos_number"   : collection.photo_set.all().count(),
                "user_first_name" : collection.user.first_name,
                "user_last_name"  : collection.user.last_name,
                'tags'            : [tag.name for tag in collection.photo_set.filter().first().hashtag.all()[:self.LIMIT_NUM]]
            } for collection in collections]

            return JsonResponse({'data' : result}, status=200)
        except ValueError:
            return JsonResponse({"message" : "INVALID_KEY"}, status=400)

class SearchBarView(View):
    def get(self, request):
        result = list(HashTag.objects.all().order_by('name').values_list('name', flat=True))
        return JsonResponse({"data" : result}, status=200)

class UserCardView(View):
    PHOTO_LIMIT = 3

    @login_check
    def get(self, request, user_id, user_name):
        try:
            user = User.objects.prefetch_related("photo_set", "following").get(user_name=user_name)

            result = {
                "id"                    : user.id,
                "user_first_name"       : user.first_name,
                "user_last_name"        : user.last_name,
                "user_name"             : user.user_name,
                "user_profile_image"    : user.profile_image,
                "photos"                : [photo.image for photo in user.photo_set.all()[:self.PHOTO_LIMIT]],
            }

            if user.id != user_id:
                result['follow'] = user.follower.filter(from_user_id=user_id, status=True).exists()
            else:
                result['follow'] = 'self'

            return JsonResponse({'data' : result}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'message' : 'NON_EXISTING_USER'}, status=401)

class UploadView(View):
    @login_check
    def post(self, request, user_id):
        try:
            if user_id:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id       = AWS_S3['access_key'],
                    aws_secret_access_key   = AWS_S3['secret_access_key']
                )

                url_id = str(uuid.uuid4().int)

                s3_client.upload_fileobj(
                    request.FILES['filename'],
                    'weplash',
                    url_id,
                    ExtraArgs={
                        "ContentType" : request.FILES['filename'].content_type
                    }
                )
                data = request.POST.dict()

                image = Image.open(urlopen(S3_URL+url_id))

                photo = Photo.objects.create(
                    user_id     = user_id,
                    image       = S3_URL+url_id,
                    location    = data['location'],
                    width       = image.width,
                    height      = image.height
                )
                upload_image.delay(photo.image, data)
                return HttpResponse(status=200)
            return JsonResponse({'message' : 'UNAUTHORIZED'}, status=401)
        except KeyError:
            return JsonResponse({'message' : "KEY_ERROR"}, status=400)


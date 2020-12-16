from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        print(username, password)
        try:
            player = UserModel.objects.get(email=username)
            if player.check_password(password):
                return player
        except UserModel.DoesNotExist:
            return None

    # def get_user(self, user_id):
    #     try:
    #         user = UserModel.objects.get(pk=user_id)
    #     except UserModel.DoesNotExist:
    #         return None
    #     return user if self.user_can_authenticate(user) else None

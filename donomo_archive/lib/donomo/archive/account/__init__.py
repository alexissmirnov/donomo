from django.contrib.auth.models import User
#
# pylint: disable-msg = E1101, W0232
#
#    E1101 : Class 'User' has no 'DoesNotExist' member
#    W0232 : OpenIDAuthBackend: Class has no __init__ method


class OpenIDAuthBackend:
    def authenticate(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        plan = getattr(getattr(user, "profile", None), "plan", "free")
        token["plan"] = plan  # 선택: 토큰에 등급 심기
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        profile = getattr(user, "profile", None)
        data.update({
            "username": user.username,
            "name": user.first_name,
            "plan": getattr(profile, "plan", "free"),
            "pro_badge": getattr(profile, "has_pro_badge", False),
        })
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

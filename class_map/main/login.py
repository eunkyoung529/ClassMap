from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile, Plan

# 회원가입 시 입력: 아이디(username), 이름(name), 비밀번호/확인, 결제금액(paid_amount)
# paid_amount가 10,000원 이상이면 Pro, 그 미만/미입력은 일반로 저장.

class RegisterSerializer(serializers.ModelSerializer):
    # 클라이언트 입력 필드
    name = serializers.CharField(write_only=True, required=True)          # 표시용 이름(-> first_name 저장)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    paid_amount = serializers.IntegerField(write_only=True, required=False, min_value=0)  # 결제금액(원)

    class Meta:
        model = User
        # username=아이디, name=이름, password/2, paid_amount
        fields = ("username", "name", "password", "password2", "paid_amount")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "비밀번호 확인이 일치하지 않습니다."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        name = validated_data.pop("name")
        validated_data.pop("password2")
        paid_amount = validated_data.pop("paid_amount", 0)
        raw_password = validated_data.pop("password")

        # User 생성
        user = User(**validated_data)
        user.first_name = name             # 이름 저장 (원하면 last_name 분리 가능)
        user.set_password(raw_password)
        user.save()

        # Profile(plan) 결정: 10,000원 이상이면 Pro, 아니면 일반
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.plan = Plan.PRO if (paid_amount and paid_amount >= 10000) else Plan.FREE
        profile.save(update_fields=["plan"])

        return user

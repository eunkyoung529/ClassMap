from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class LectureReview(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    professor = models.CharField(max_length=255)
    rating = models.SmallIntegerField()
    semester = models.CharField(max_length=50) 
    content = models.TextField()

    def __str__(self):
        return f"{self.title}: {self.professor}({self.semester})"
    



#로그인/회원가입 시 일반/pro 구분 

class Plan(models.TextChoices):
    FREE = "free", "일반"
    PRO  = "pro",  "Pro"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.FREE)

    def __str__(self):
        return f"{self.user.username} ({self.get_plan_display()})"

    @property
    def has_pro_badge(self) -> bool:
        return self.plan == Plan.PRO


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)

 




# history 추상 모델
class BaseChatHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name = "사용자"
    )
    query = models.TextField(verbose_name="사용자 질문")
    response = models.TextField(verbose_name="챗봇 답변")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        abstract = True # 추상 모델 명시
        ordering = ['-created_at'] # 최신순 정렬

# 공모전/대회 추천 챗봇 히스토리 모델
class ActivityChatHistory(BaseChatHistory):
    def __str__(self):
        return f"{self.user.username}님의 공모전/대회 챗봇 질문 (ID: {self.id})"
    
    class Meta(BaseChatHistory.Meta):
        verbose_name = "공모전/대회 챗봇 히스토리" # 단수형 이름
        verbose_name_plural = "공모전/대회 챗봇 히스토리 목록" # 복수형 이름

# 강의 추천 챗봇 히스토리 모델
class LectureChatHistory(BaseChatHistory):
    def __str__(self):
        return f"{self.user.username}님의 강의 챗봇 질문 (ID: {self.id})"

    class Meta(BaseChatHistory.Meta):
        verbose_name = "강의 챗봇 히스토리"
        verbose_name_plural = "강의 챗봇 히스토리 목록"

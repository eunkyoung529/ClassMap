from django.db import models

class LectureReview(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    professor = models.CharField(max_length=255)
    rating = models.SmallIntegerField()
    semester = models.CharField(max_length=50) 
    content = models.TextField()

    def __str__(self):
        return f"{self.title}: {self.professor}({self.semester})"
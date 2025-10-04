import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from main.models import LectureReview

# CSV 파일에서 수강평 데이터를 읽어와 db에 저장해주는 command
class Command(BaseCommand): # python manage.py import_reviews
    help = "Import lecture reviews from CSV" # baseCommand 입력시 출력되는 설명

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, help="Path to CSV", required=False) # python manage.py import_reviews --path <경로>
    
    def handle(self, *args, **opts):
        # --path 옵션이 있으면 그것 사용, 없으면 settings 값 사용
        path = opts.get("path") or settings.CSV_REVIEWS_PATH
        p = Path(path)

        if not p.exists():
            raise CommandError(f"CSV not found: {p}")
        
        created, updated = 0, 0 # 생성된 개수, 업데이트된 개수
        # CSV 파일 읽어서 DB에 저장
        with p.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                is_created = LectureReview.objects.update_or_create(
                    title=row["title"],
                    professor=row["professor"],
                    semester=row["semester"],
                    # 새 데이터가 기존 데이터의 title, professor, semester와 같으면 해당 행의 defaults를 업데이트, 다르면 새로 생성
                    defaults={
                        "rating": row["rating"],
                        "content": row["content"]
                    }
                )
                if is_created: # 새로 생성된 경우
                    created += 1
                else: # 기존에 있던 경우
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {created} reviews"))
        if updated:
            self.stdout.write(self.style.WARNING(f"Updated {updated} existing reviews"))
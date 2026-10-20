import sys
from pathlib import Path
from datetime import datetime

# Đảm bảo import được module backend
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import inspect, text
from backend.database import engine, DATABASE_URL, Base, SessionLocal
import backend.models as models
from backend.security import get_password_hash


def init_database():
    """
    Tạo toàn bộ schema bảng và nạp Seed Data mẫu cho hệ thống:
    1. Users: Admin và Candidate
    2. Industries & 9 Positions
    3. Ngân hàng câu hỏi phân theo 5 level
    4. 5 phiên phỏng vấn mẫu đã hoàn thành
    """
    safe_url = DATABASE_URL
    if "@" in safe_url and ":" in safe_url:
        try:
            prefix, rest = safe_url.split("://", 1)
            creds, host_part = rest.split("@", 1)
            user = creds.split(":", 1)[0]
            safe_url = f"{prefix}://{user}:****@{host_part}"
        except Exception:
            pass

    print(f"🔗 Đang kết nối tới Database: {safe_url}")
    print("⏳ Đang ánh xạ ORM Models sang các bảng...")

    Base.metadata.create_all(bind=engine)

    # Tự động cập nhật cột thiếu cho DB cũ nếu có
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        with engine.connect() as conn:
            if "session_details" in table_names:
                columns = [c["name"] for c in inspector.get_columns("session_details")]
                if "video_url" not in columns:
                    print("⚡ Bổ sung cột video_url trong session_details...")
                    conn.execute(text("ALTER TABLE session_details ADD COLUMN video_url VARCHAR(500);"))
                    conn.commit()
            if "interview_sessions" in table_names:
                columns = [c["name"] for c in inspector.get_columns("interview_sessions")]
                if "level" not in columns:
                    print("⚡ Bổ sung cột level trong interview_sessions...")
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN level VARCHAR(50) DEFAULT 'junior';"))
                    conn.commit()
    except Exception as e:
        print(f"⚠️ Kiểm tra nâng cấp cột: {e}")

    # Seed data
    db = SessionLocal()
    try:
        # 1. Seed Users
        admin_pass = get_password_hash("Admin@123456")
        cand_pass = get_password_hash("Candidate@123456")

        users_to_seed = [
            {
                "id": "admin_123",
                "email": "admin@mockinterview.ai",
                "full_name": "Quản trị viên Hệ thống",
                "role": "ADMIN",
                "hashed_password": admin_pass,
            },
            {
                "id": "admin_test",
                "email": "admin@interviewlab.test",
                "full_name": "Quản trị viên Hệ thống (Test)",
                "role": "ADMIN",
                "hashed_password": admin_pass,
            },
            {
                "id": "user_123",
                "email": "candidate@mockinterview.ai",
                "full_name": "Nguyễn Minh Đức",
                "phone_number": "0912345678",
                "role": "USER",
                "hashed_password": cand_pass,
            },
            {
                "id": "user_test",
                "email": "candidate@interviewlab.test",
                "full_name": "Nguyễn Minh Đức (Test)",
                "phone_number": "0912345678",
                "role": "USER",
                "hashed_password": cand_pass,
            },
        ]

        for u_data in users_to_seed:
            existing_user = db.query(models.User).filter(
                (models.User.id == u_data["id"]) | (models.User.email == u_data["email"])
            ).first()
            if not existing_user:
                db.add(models.User(**u_data))

        # 2. Seed Industries
        industries_data = [
            {"id": "it", "code": "IT", "name": "Công nghệ thông tin"},
            {"id": "data", "code": "DATA", "name": "Phân tích dữ liệu"},
            {"id": "sales", "code": "SALES", "name": "Kinh doanh"},
            {"id": "hr", "code": "HR", "name": "Nhân sự"},
        ]
        for ind in industries_data:
            existing_ind = db.query(models.Industry).filter_by(id=ind["id"]).first()
            if not existing_ind:
                db.add(models.Industry(**ind))

        db.flush()

        # 3. Seed Positions
        positions_data = [
            {"id": "backend", "industry_id": "it", "name": "Backend Developer", "skills": ["Python", "FastAPI", "SQL"], "duration": "3–6 tháng", "icon": "server"},
            {"id": "frontend", "industry_id": "it", "name": "Frontend Developer", "skills": ["React", "JavaScript", "CSS"], "duration": "3–6 tháng", "icon": "layout"},
            {"id": "data-analyst", "industry_id": "data", "name": "Data Analyst", "skills": ["SQL", "Python", "Tableau"], "duration": "3–6 tháng", "icon": "chart"},
            {"id": "business-analyst", "industry_id": "it", "name": "Business Analyst", "skills": ["SQL", "BPMN", "User Story"], "duration": "6–12 tháng", "icon": "briefcase"},
            {"id": "ai-engineer", "industry_id": "it", "name": "AI Engineer", "skills": ["Python", "PyTorch", "LLM"], "duration": "6–12 tháng", "icon": "brain"},
            {"id": "system-analyst", "industry_id": "it", "name": "System Analyst", "skills": ["UML", "Architecture", "API"], "duration": "1–3 năm", "icon": "network"},
            {"id": "sales", "industry_id": "sales", "name": "Sales / Business Development", "skills": ["Đàm phán", "Bán hàng B2B"], "duration": "3–6 tháng", "icon": "trend"},
            {"id": "marketing", "industry_id": "sales", "name": "Marketing", "skills": ["Content", "SEO", "Facebook Ads"], "duration": "3–6 tháng", "icon": "megaphone"},
            {"id": "hr", "industry_id": "hr", "name": "Human Resources (HR)", "skills": ["Tuyển dụng", "Phỏng vấn"], "duration": "3–6 tháng", "icon": "users"},
        ]
        for pos in positions_data:
            existing_pos = db.query(models.Position).filter_by(id=pos["id"]).first()
            if not existing_pos:
                db.add(models.Position(**pos))

        db.flush()

        # 4. Seed Questions
        level_groups = {
            "all": ["intern", "fresher", "junior", "mid", "senior"],
            "entry": ["intern", "fresher"],
            "junior": ["junior"],
            "mid": ["mid"],
            "senior": ["senior"],
        }

        bank = {
            "backend": {
                "all": [
                    ("Hành vi", "Bạn hãy giới thiệu bản thân và dự án backend ấn tượng nhất bạn từng tham gia?"),
                    ("Hành vi", "Khi gặp lỗi nghiêm trọng sát giờ bàn giao, bạn ứng phó thế nào?"),
                ],
                "entry": [
                    ("Chuyên môn", "REST API là gì? Phân biệt các phương thức GET, POST, PUT, DELETE."),
                    ("Chuyên môn", "Sự khác biệt giữa SQL và NoSQL là gì? Khi nào dùng loại nào?"),
                ],
                "junior": [
                    ("Chuyên môn", "Giải thích index trong cơ sở dữ liệu và khi nào index làm chậm hệ thống."),
                    ("Chuyên môn", "Sự khác biệt giữa xử lý bất đồng bộ (Async) và đa luồng (Multithread) là gì?"),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn thiết kế cơ chế caching cho API có lưu lượng đọc lớn như thế nào?"),
                    ("Tình huống", "API chính chậm đột ngột trên production, bạn điều tra theo các bước nào?"),
                ],
                "senior": [
                    ("Thiết kế", "Bạn sẽ tách một monolith thành microservices theo tiêu chí và lộ trình nào?"),
                    ("Lãnh đạo", "Bạn review code và định hướng kỹ thuật cho team như thế nào?"),
                ],
            },
            "frontend": {
                "all": [
                    ("Hành vi", "Hãy kể về một giao diện bạn tự hào nhất và vai trò của bạn trong đó."),
                    ("Hành vi", "Bạn xử lý thế nào khi designer và bạn bất đồng về cách hiện thực giao diện?"),
                ],
                "entry": [
                    ("Chuyên môn", "Phân biệt state và props trong React."),
                    ("Chuyên môn", "Box model trong CSS là gì? Phân biệt flexbox và grid."),
                ],
                "junior": [
                    ("Chuyên môn", "useEffect hoạt động ra sao và những lỗi thường gặp với dependency array?"),
                    ("Chuyên môn", "Bạn tối ưu hiệu năng render của một danh sách dài như thế nào?"),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn chọn giải pháp quản lý state toàn cục dựa trên tiêu chí nào?"),
                    ("Tình huống", "Trang web tải chậm trên di động, bạn phân tích và cải thiện ra sao?"),
                ],
            },
            "data-analyst": {
                "all": [
                    ("Hành vi", "Hãy kể về một lần phân tích dữ liệu giúp đưa ra quyết định quan trọng."),
                    ("Hành vi", "Bạn trình bày kết quả phân tích cho người không có chuyên môn kỹ thuật như thế nào?"),
                ],
                "entry": [
                    ("Chuyên môn", "Phân biệt INNER JOIN và LEFT JOIN trong SQL."),
                    ("Chuyên môn", "Bạn xử lý dữ liệu thiếu và dữ liệu ngoại lai như thế nào?"),
                ],
                "junior": [
                    ("Chuyên môn", "Window function là gì? Cho ví dụ ứng dụng thực tế."),
                    ("Chuyên môn", "Bạn chọn loại biểu đồ nào để thể hiện xu hướng và so sánh theo nhóm?"),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn thiết kế A/B test và đánh giá ý nghĩa thống kê như thế nào?"),
                    ("Tình huống", "Số liệu doanh thu giữa hai báo cáo không khớp nhau, bạn xử lý ra sao?"),
                ],
            },
            "business-analyst": {
                "all": [
                    ("Hành vi", "Hãy giới thiệu một dự án bạn đã làm cầu nối giữa nghiệp vụ và kỹ thuật."),
                    ("Hành vi", "Bạn xử lý thế nào khi các bên liên quan có yêu cầu mâu thuẫn nhau?"),
                ],
                "junior": [
                    ("Chuyên môn", "Phân biệt functional và non-functional requirements, cho ví dụ."),
                    ("Chuyên môn", "User story tốt cần có những thành phần nào?"),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn ưu tiên backlog bằng phương pháp nào (MoSCoW, RICE,...)?"),
                    ("Tình huống", "Khách hàng liên tục thay đổi yêu cầu giữa sprint, bạn xử lý ra sao?"),
                ],
                "senior": [
                    ("Chiến lược", "Bạn xây dựng business case để thuyết phục ban lãnh đạo đầu tư dự án như thế nào?"),
                    ("Lãnh đạo", "Bạn dẫn dắt và đào tạo BA mới trong team như thế nào?"),
                ],
            },
            "ai-engineer": {
                "all": [
                    ("Hành vi", "Hãy kể về một mô hình AI bạn từng xây dựng và kết quả đạt được."),
                    ("Hành vi", "Bạn giải thích kết quả mô hình cho người không chuyên như thế nào?"),
                ],
                "junior": [
                    ("Chuyên môn", "Overfitting là gì? Bạn có những cách nào để giảm overfitting?"),
                    ("Chuyên môn", "Giải thích precision, recall và khi nào ưu tiên chỉ số nào."),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn triển khai và giám sát mô hình trên production như thế nào?"),
                    ("Tình huống", "Độ chính xác của mô hình giảm dần sau vài tháng, bạn điều tra ra sao?"),
                ],
                "senior": [
                    ("Thiết kế", "Bạn thiết kế pipeline MLOps từ thu thập dữ liệu đến triển khai như thế nào?"),
                    ("Chiến lược", "Bạn cân nhắc thế nào giữa tự huấn luyện mô hình và dùng API LLM có sẵn?"),
                ],
            },
            "system-analyst": {
                "all": [
                    ("Hành vi", "Hãy kể về hệ thống phức tạp nhất bạn từng phân tích và thiết kế."),
                    ("Hành vi", "Bạn phối hợp với đội phát triển và khách hàng như thế nào để tránh hiểu sai yêu cầu?"),
                ],
                "mid": [
                    ("Chuyên môn", "Bạn dùng những sơ đồ UML nào để mô tả một hệ thống và vì sao?"),
                    ("Chuyên môn", "Phân biệt use case diagram và sequence diagram."),
                ],
                "senior": [
                    ("Thiết kế", "Bạn đánh giá và lựa chọn kiến trúc cho hệ thống cần tích hợp nhiều dịch vụ cũ như thế nào?"),
                    ("Chiến lược", "Bạn quản lý nợ kỹ thuật và rủi ro khi di chuyển hệ thống cũ ra sao?"),
                ],
            },
            "sales": {
                "all": [
                    ("Hành vi", "Hãy giới thiệu bản thân và lý do bạn chọn công việc kinh doanh."),
                    ("Hành vi", "Kể về một lần bạn bị khách hàng từ chối và bạn đã phản ứng thế nào."),
                ],
                "entry": [
                    ("Chuyên môn", "Bạn tìm hiểu nhu cầu khách hàng trước khi giới thiệu sản phẩm như thế nào?"),
                    ("Tình huống", "Khách hàng nói giá sản phẩm quá cao, bạn trả lời ra sao?"),
                ],
                "junior": [
                    ("Chuyên môn", "Bạn xây dựng và duy trì pipeline khách hàng tiềm năng như thế nào?"),
                    ("Tình huống", "Bạn làm gì khi sắp không đạt chỉ tiêu doanh số trong tháng?"),
                ],
                "mid": [
                    ("Chiến lược", "Bạn xây dựng kế hoạch chinh phục một khách hàng doanh nghiệp lớn như thế nào?"),
                    ("Lãnh đạo", "Bạn hỗ trợ đồng nghiệp mới đạt hiệu suất bán hàng ra sao?"),
                ],
            },
            "marketing": {
                "all": [
                    ("Hành vi", "Hãy giới thiệu một chiến dịch marketing bạn ấn tượng và lý do."),
                    ("Hành vi", "Bạn xử lý thế nào khi chiến dịch không đạt kết quả như kỳ vọng?"),
                ],
                "entry": [
                    ("Chuyên môn", "Phân biệt các kênh marketing: SEO, SEM và social media."),
                    ("Chuyên môn", "Bạn xác định chân dung khách hàng mục tiêu (persona) như thế nào?"),
                ],
                "junior": [
                    ("Chuyên môn", "Bạn đo lường hiệu quả chiến dịch bằng những chỉ số nào (CTR, CAC, ROAS,...)?"),
                    ("Tình huống", "Ngân sách bị cắt 30%, bạn điều chỉnh chiến dịch ra sao?"),
                ],
                "mid": [
                    ("Chiến lược", "Bạn xây dựng chiến lược ra mắt sản phẩm mới trên thị trường cạnh tranh như thế nào?"),
                    ("Lãnh đạo", "Bạn phân bổ ngân sách giữa các kênh và đánh giá hiệu quả ra sao?"),
                ],
            },
            "hr": {
                "all": [
                    ("Hành vi", "Hãy giới thiệu bản thân và động lực chọn làm việc trong lĩnh vực nhân sự."),
                    ("Hành vi", "Kể về một tình huống khó trong giao tiếp với nhân viên và cách bạn xử lý."),
                ],
                "entry": [
                    ("Chuyên môn", "Quy trình tuyển dụng cơ bản gồm những bước nào?"),
                    ("Tình huống", "Bạn sàng lọc hồ sơ ứng viên như thế nào khi nhận được hàng trăm CV?"),
                ],
                "junior": [
                    ("Chuyên môn", "Bạn đặt câu hỏi phỏng vấn theo hành vi (STAR) như thế nào?"),
                    ("Tình huống", "Nhân viên giỏi nộp đơn nghỉ việc, bạn xử lý ra sao?"),
                ],
                "mid": [
                    ("Chiến lược", "Bạn xây dựng chương trình giữ chân nhân tài như thế nào?"),
                    ("Chuyên môn", "Bạn thiết kế quy trình đánh giá hiệu suất công bằng ra sao?"),
                ],
            },
        }

        for pos_id, groups in bank.items():
            seq = 0
            for group, items in groups.items():
                lvs = level_groups[group]
                for cat, q_text in items:
                    seq += 1
                    q_id = f"{pos_id}-{seq}"
                    existing_q = db.query(models.Question).filter_by(id=q_id).first()
                    if not existing_q:
                        db.add(
                            models.Question(
                                id=q_id,
                                position_id=pos_id,
                                category=cat,
                                question_text=q_text,
                                time_limit_seconds=120,
                                level=lvs[0],
                                levels=lvs,
                            )
                        )

        # 5. Seed 5 Interview Sessions mẫu
        sample_sessions = [
            {
                "id": "mock_result_1",
                "user_id": "user_123",
                "role_name": "Backend Developer",
                "level": "fresher",
                "overall_score": 85.0,
                "confidence_avg": 84.0,
                "stress_avg": 20.0,
                "status": "COMPLETED",
                "created_at": datetime.fromisoformat("2026-10-17T10:32:00"),
                "details": [
                    {
                        "question_text": "REST API là gì? Phân biệt các phương thức GET, POST, PUT, DELETE.",
                        "order_index": 1,
                        "transcript": "REST API là giao diện lập trình ứng dụng tuân thủ các nguyên tắc REST...",
                        "filler_words_count": 2,
                        "confidence_score": 88.0,
                        "stress_score": 15.0,
                        "content_score": 92.0,
                        "ai_feedback": {
                            "content_critique": "Nội dung chuẩn xác, phân biệt rõ các HTTP methods.",
                            "delivery_critique": "Tốc độ nói vừa phải, phát âm rõ ràng.",
                            "suggested_answer": "Có thể bổ sung thêm Idempotent methods.",
                        },
                        "video_url": "https://storage.googleapis.com/mock-interview-lab/sample1.mp4",
                        "status": "COMPLETED",
                    }
                ],
            },
            {
                "id": "mock_result_2",
                "user_id": "user_123",
                "role_name": "Data Analyst",
                "level": "junior",
                "overall_score": 78.0,
                "confidence_avg": 76.0,
                "stress_avg": 35.0,
                "status": "COMPLETED",
                "created_at": datetime.fromisoformat("2026-10-14T16:18:00"),
                "details": [],
            },
            {
                "id": "mock_result_3",
                "user_id": "user_123",
                "role_name": "Marketing",
                "level": "intern",
                "overall_score": 82.0,
                "confidence_avg": 81.0,
                "stress_avg": 25.0,
                "status": "COMPLETED",
                "created_at": datetime.fromisoformat("2026-10-10T09:45:00"),
                "details": [],
            },
            {
                "id": "mock_result_4",
                "user_id": "user_123",
                "role_name": "Backend Developer",
                "level": "intern",
                "overall_score": 70.0,
                "confidence_avg": 70.0,
                "stress_avg": 55.0,
                "status": "COMPLETED",
                "created_at": datetime.fromisoformat("2026-10-05T20:10:00"),
                "details": [],
            },
            {
                "id": "mock_result_5",
                "user_id": "user_123",
                "role_name": "Frontend Developer",
                "level": "intern",
                "overall_score": 66.0,
                "confidence_avg": 65.0,
                "stress_avg": 60.0,
                "status": "COMPLETED",
                "created_at": datetime.fromisoformat("2026-10-01T09:00:00"),
                "details": [],
            },
        ]

        for s_data in sample_sessions:
            existing_sess = db.query(models.InterviewSession).filter_by(id=s_data["id"]).first()
            if not existing_sess:
                details = s_data.pop("details", [])
                sess = models.InterviewSession(**s_data)
                db.add(sess)
                db.flush()
                for d in details:
                    d["session_id"] = sess.id
                    db.add(models.SessionDetail(**d))

        db.commit()
        print("✅ NẠP DỮ LIỆU SEED DATA THÀNH CÔNG:")
        print(f"   - Users: {db.query(models.User).count()} bản ghi")
        print(f"   - Industries: {db.query(models.Industry).count()} bản ghi")
        print(f"   - Positions: {db.query(models.Position).count()} bản ghi")
        print(f"   - Questions: {db.query(models.Question).count()} bản ghi")
        print(f"   - Sessions: {db.query(models.InterviewSession).count()} bản ghi")

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi nạp Seed Data: {e}")
        raise e
    finally:
        db.close()

    print("\n✅ ÁNH XẠ THÀNH CÔNG! Danh sách các bảng đã được đồng bộ:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - 📋 Bảng: {table_name}")
    print("\n🎉 Cơ sở dữ liệu đã sẵn sàng cho ứng dụng!")


if __name__ == "__main__":
    init_database()

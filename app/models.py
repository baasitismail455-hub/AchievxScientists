from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, default="")
    avatar = db.Column(db.String(300))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def initials(self):
        parts = (self.name or self.username).split()
        return "".join(p[0] for p in parts[:2]).upper()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(210), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, default="")
    aims = db.Column(db.Text, default="")
    discipline = db.Column(db.String(100), default="")
    status = db.Column(db.String(30), default="Ongoing", nullable=False)
    collaboration_type = db.Column(db.String(30), default="Independent", nullable=False)
    visibility = db.Column(db.String(20), default="Public", nullable=False)
    cover_image = db.Column(db.String(300))
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    owner = db.relationship("User", backref=db.backref("owned_projects", lazy=True))
    updates = db.relationship("ProjectUpdate", backref="project", cascade="all, delete-orphan",
                              order_by="ProjectUpdate.created_at.desc()")
    collaborators = db.relationship("ProjectMember", backref="project", cascade="all, delete-orphan")

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(30), default="Collaborator", nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("memberships", lazy=True))
    __table_args__ = (db.UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

class ProjectInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    invited_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    project = db.relationship("Project", backref=db.backref("invitations", cascade="all, delete-orphan"))
    invited_by = db.relationship("User")

class ProjectUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, default="")
    update_type = db.Column(db.String(40), default="Progress update")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    author = db.relationship("User", backref=db.backref("project_updates", lazy=True))
    attachments = db.relationship("Attachment", backref="update", cascade="all, delete-orphan")

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.Integer, db.ForeignKey("project_update.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(300), nullable=False, unique=True)
    mime_type = db.Column(db.String(150), default="application/octet-stream")
    size_bytes = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None

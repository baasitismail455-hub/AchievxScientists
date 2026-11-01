import os, re, uuid
from pathlib import Path
from datetime import datetime
from flask import (render_template, request, redirect, url_for, flash, abort,
                   current_app, send_from_directory)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import db
from app.models import User, Project, ProjectMember, ProjectInvitation, ProjectUpdate, Attachment

from app.models import User, Project, ProjectMember, ProjectInvitation, ProjectUpdate, Attachment
# Route and error-handler registration for the Flask application factory.
_route_rules = []
_error_handlers = []


def route(rule, **options):
    def decorator(view_func):
        _route_rules.append((rule, view_func, options))
        return view_func
    return decorator


def errorhandler(code):
    def decorator(handler_func):
        _error_handlers.append((code, handler_func))
        return handler_func
    return decorator

ALLOWED_EXTENSIONS = {
    "png","jpg","jpeg","gif","webp","pdf","csv","tsv","xlsx","xls","doc","docx",
    "ppt","pptx","txt","md","rtf","json","zip","mp3","wav","m4a","ogg","mp4","mov","webm"
}
IMAGE_EXTENSIONS = {"png","jpg","jpeg","gif","webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value[:180] or "project"

def unique_slug(title):
    base = slugify(title)
    slug = base
    n = 2
    while Project.query.filter_by(slug=slug).first():
        slug = f"{base}-{n}"
        n += 1
    return slug

def is_member(project):
    if not current_user.is_authenticated:
        return False
    if current_user.is_admin or project.owner_id == current_user.id:
        return True
    return ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first() is not None

def can_view(project):
    return project.visibility == "Public" or is_member(project)

def require_project_access(project):
    if not can_view(project):
        abort(403)

def save_upload(file, folder_prefix):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed: {file.filename}")
    original = secure_filename(file.filename)[:255] or "upload"
    stored = f"{folder_prefix}_{uuid.uuid4().hex}_{original}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored))
    return original, stored, file.mimetype or "application/octet-stream", os.path.getsize(
        os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
    )

def inject_globals():
    return {"site_name": current_app.config.get("SITE_NAME", "AchievX Scientist")}

@route("/")
def home():
    query = request.args.get("q", "").strip()
    projects_query = Project.query.filter_by(visibility="Public")
    if query:
        like = f"%{query}%"
        projects_query = projects_query.filter(or_(
            Project.title.ilike(like), Project.summary.ilike(like),
            Project.discipline.ilike(like), Project.description.ilike(like)
        ))
    projects = projects_query.order_by(Project.updated_at.desc()).all()
    return render_template("home.html", projects=projects, query=query)

@route("/about")
def about():
    return render_template("about.html")

@route("/register", methods=["GET", "POST"])
def auth_register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not username or not email or len(password) < 10:
            flash("Complete all fields. Passwords must contain at least 10 characters.", "error")
        elif User.query.filter(or_(User.email == email, User.username == username)).first():
            flash("That email address or username is already registered.", "error")
        else:
            user = User(name=name, username=username, email=email)
            user.set_password(password)
            if User.query.count() == 0:
                user.is_admin = True
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account is ready. Welcome to AchievX Scientist.", "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@route("/login", methods=["GET", "POST"])
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        user = User.query.filter(or_(User.email == identity, User.username == identity)).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("The sign-in details were not recognised.", "error")
    return render_template("auth.html", mode="login")

@route("/logout")
@login_required
def auth_logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))

@route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        projects = Project.query.order_by(Project.updated_at.desc()).all()
    else:
        ids = [m.project_id for m in current_user.memberships]
        projects = Project.query.filter(or_(Project.owner_id == current_user.id,
                                            Project.id.in_(ids))).order_by(Project.updated_at.desc()).all()
    invitations = ProjectInvitation.query.filter_by(email=current_user.email, status="Pending").all()
    return render_template("dashboard.html", projects=projects, invitations=invitations)

@route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        summary = request.form.get("summary", "").strip()
        if not title or not summary:
            flash("Project title and card summary are required.", "error")
        else:
            project = Project(
                title=title, slug=unique_slug(title), summary=summary,
                description=request.form.get("description", "").strip(),
                aims=request.form.get("aims", "").strip(),
                discipline=request.form.get("discipline", "").strip(),
                status=request.form.get("status", "Ongoing"),
                collaboration_type=request.form.get("collaboration_type", "Independent"),
                visibility=request.form.get("visibility", "Public"),
                owner_id=current_user.id
            )
            cover = request.files.get("cover_image")
            if cover and cover.filename:
                try:
                    ext = cover.filename.rsplit(".", 1)[-1].lower() if "." in cover.filename else ""
                    if ext not in IMAGE_EXTENSIONS:
                        raise ValueError("Project cover images must be PNG, JPG, GIF or WebP.")
                    result = save_upload(cover, "cover")
                    if result:
                        project.cover_image = result[1]
                except ValueError as e:
                    flash(str(e), "error")
                    return render_template("project_form.html", project=None)
            db.session.add(project)
            db.session.commit()
            flash("Project created. You can now add progress updates and research materials.", "success")
            return redirect(url_for("project_detail", slug=project.slug))
    return render_template("project_form.html", project=None)

@route("/projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()
    require_project_access(project)
    pending_invite = None
    if current_user.is_authenticated:
        pending_invite = ProjectInvitation.query.filter_by(
            project_id=project.id, email=current_user.email, status="Pending"
        ).first()
    return render_template("project_detail.html", project=project, member=is_member(project),
                           pending_invite=pending_invite)

@route("/projects/<slug>/edit", methods=["GET", "POST"])
@login_required
def project_edit(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()
    if not (current_user.is_admin or project.owner_id == current_user.id):
        abort(403)
    if request.method == "POST":
        project.title = request.form.get("title", "").strip() or project.title
        project.summary = request.form.get("summary", "").strip() or project.summary
        project.description = request.form.get("description", "").strip()
        project.aims = request.form.get("aims", "").strip()
        project.discipline = request.form.get("discipline", "").strip()
        project.status = request.form.get("status", project.status)
        project.collaboration_type = request.form.get("collaboration_type", project.collaboration_type)
        project.visibility = request.form.get("visibility", project.visibility)
        cover = request.files.get("cover_image")
        if cover and cover.filename:
            try:
                result = save_upload(cover, "cover")
                if result:
                    project.cover_image = result[1]
            except ValueError as e:
                flash(str(e), "error")
                return render_template("project_form.html", project=project)
        project.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Project details updated.", "success")
        return redirect(url_for("project_detail", slug=project.slug))
    return render_template("project_form.html", project=project)

@route("/projects/<slug>/updates/new", methods=["POST"])
@login_required
def update_new(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()
    if not is_member(project):
        abort(403)
    title = request.form.get("title", "").strip()
    if not title:
        flash("Give this progress entry a title.", "error")
        return redirect(url_for("project_detail", slug=slug) + "#add-update")
    update = ProjectUpdate(project=project, author=current_user, title=title,
                           body=request.form.get("body", "").strip(),
                           update_type=request.form.get("update_type", "Progress update"))
    db.session.add(update)
    db.session.flush()
    try:
        for file in request.files.getlist("files"):
            result = save_upload(file, f"project{project.id}")
            if result:
                original, stored, mime, size = result
                db.session.add(Attachment(update=update, original_name=original,
                                          stored_name=stored, mime_type=mime, size_bytes=size))
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("project_detail", slug=slug) + "#add-update")
    project.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Progress update saved with its attached materials.", "success")
    return redirect(url_for("project_detail", slug=slug) + f"#update-{update.id}")

@route("/projects/<slug>/invite", methods=["POST"])
@login_required
def invite_collaborator(slug):
    project = Project.query.filter_by(slug=slug).first_or_404()
    if not (current_user.is_admin or project.owner_id == current_user.id):
        abort(403)
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        flash("Enter a valid collaborator email address.", "error")
    elif email == current_user.email:
        flash("You are already the project owner.", "error")
    else:
        existing = ProjectInvitation.query.filter_by(project_id=project.id, email=email, status="Pending").first()
        user = User.query.filter_by(email=email).first()
        if user and ProjectMember.query.filter_by(project_id=project.id, user_id=user.id).first():
            flash("That person is already a collaborator.", "info")
        elif not existing:
            db.session.add(ProjectInvitation(project_id=project.id, email=email,
                                              invited_by_id=current_user.id))
            db.session.commit()
            flash("Invitation created. The person can register with this email or sign in to accept it.", "success")
        else:
            flash("An invitation for that email is already pending.", "info")
    return redirect(url_for("project_detail", slug=slug) + "#collaborators")

@route("/invitations/<int:invitation_id>/accept", methods=["POST"])
@login_required
def accept_invitation(invitation_id):
    invitation = ProjectInvitation.query.get_or_404(invitation_id)
    if invitation.email != current_user.email or invitation.status != "Pending":
        abort(403)
    if not ProjectMember.query.filter_by(project_id=invitation.project_id, user_id=current_user.id).first():
        db.session.add(ProjectMember(project_id=invitation.project_id, user_id=current_user.id))
    invitation.status = "Accepted"
    db.session.commit()
    flash("You have joined the project workspace.", "success")
    return redirect(url_for("project_detail", slug=invitation.project.slug))

@route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip() or current_user.name
        current_user.bio = request.form.get("bio", "").strip()
        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            ext = avatar.filename.rsplit(".", 1)[-1].lower() if "." in avatar.filename else ""
            if ext not in IMAGE_EXTENSIONS:
                flash("Profile photos must be PNG, JPG, GIF or WebP.", "error")
                return render_template("profile.html")
            stored = f"avatar_{current_user.id}_{uuid.uuid4().hex}.{ext}"
            avatar.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored))
            current_user.avatar = stored
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("dashboard"))
    return render_template("profile.html")

@route("/uploads/<path:filename>")
def uploaded_file(filename):
    attachment = Attachment.query.filter_by(stored_name=filename).first()
    if attachment:
        project = attachment.update.project
        require_project_access(project)
    else:
        project = Project.query.filter_by(cover_image=filename).first()
        user = User.query.filter_by(avatar=filename).first()
        if not project and not user:
            abort(404)
        if project:
            require_project_access(project)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

@route("/health")
def health():
    return {"application": "AchievX Scientist", "status": "running"}

@errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to view this space."), 403

@errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="We could not find the page you requested."), 404

def register_routes(app):
    """Register application routes and handlers with the Flask app."""

    app.context_processor(inject_globals)

    for rule, view_func, options in _route_rules:
        app.add_url_rule(
            rule,
            endpoint=view_func.__name__,
            view_func=view_func,
            **options
        )

    for code, handler_func in _error_handlers:
        app.register_error_handler(code, handler_func)
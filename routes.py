from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from datetime import datetime
from werkzeug.utils import secure_filename
from .extensions import db
from .models import User, Contact, Template, Campaign, CampaignJob, SystemSetting, FestivalSettings, FestivalImage, PageVisit
from .tasks import process_campaign
import pandas as pd
import os
import json
from io import BytesIO
from flask import send_file

main_bp = Blueprint('main', __name__)

# --- Auth ---
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password: # Use hash in prod
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Login failed. Check username/password.')
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# --- Dashboard ---
@main_bp.route('/')
@login_required
def dashboard():
    # Statistics
    total_sent = db.session.query(func.sum(Campaign.sent_count)).scalar() or 0
    total_failed = db.session.query(func.sum(Campaign.failed_count)).scalar() or 0
    
    # Festival Visits
    festival_visits = PageVisit.query.filter_by(page_name='festival').count()

    stats = {
        'total_sent': total_sent,
        'total_failed': total_failed,
        'contacts': Contact.query.count(),
        'campaigns': Campaign.query.count(),
        'festival_visits': festival_visits
    }
    
    # Data for Charts
    # 1. Success Rate
    chart_success = {
        'labels': ['تم الإرسال', 'فشل الإرسال'],
        'data': [total_sent, total_failed]
    }
    
    # 2. Last 5 Campaigns Performance
    last_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
    chart_campaigns = {
        'labels': [c.name for c in reversed(last_campaigns)], # Reverse to show oldest to newest left-to-right or list logic
        'data_total': [c.total_contacts for c in reversed(last_campaigns)],
        'data_sent': [c.sent_count for c in reversed(last_campaigns)]
    }

    # Active campaigns only
    active_campaigns = Campaign.query.filter(Campaign.status.in_(['processing', 'pending'])).order_by(Campaign.created_at.desc()).all()
    
    return render_template('dashboard.html', campaigns=active_campaigns, stats=stats, chart_success=chart_success, chart_campaigns=chart_campaigns)

# --- Contacts / Excel ---
@main_bp.route('/contacts/upload', methods=['GET', 'POST'])
@login_required
def upload_contacts():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded')
            return redirect(request.url)
        
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(path)

        try:
            # Determine file type
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            
            columns = df.columns.tolist()
            # Get first 5 rows as a list of dictionaries for preview
            preview_data = df.head(5).to_dict(orient='records')
            
            return render_template('contacts_preview.html', columns=columns, filepath=path, preview_data=preview_data)
        except Exception as e:
            flash(f'Error reading file: {str(e)}')
            return redirect(request.url)

    return render_template('upload_contacts.html')

@main_bp.route('/contacts/save', methods=['POST'])
@login_required
def save_contacts():
    filepath = request.form.get('filepath')
    phone_col = request.form.get('phone_col')
    
    if not filepath or not os.path.exists(filepath):
        flash('File lost. Please upload again.')
        return redirect(url_for('main.upload_contacts'))
    
    try:
        if filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
            
        count = 0
        updated = 0
        
        for index, row in df.iterrows():
            raw_phone = str(row[phone_col])
            # Basic cleanup for storage uniqueness: remove .0 from excel floats, strip spaces
            # We do NOT normalize here (e.g. adding +968) to allow flexible sending logic later
            clean_phone = raw_phone.replace('.0', '').strip().replace(' ', '').replace('-', '')
            
            # Store all other data as JSON
            other_data = row.to_dict()
            if phone_col in other_data:
                del other_data[phone_col]
            
            contact = Contact.query.filter_by(phone=clean_phone).first()
            if contact:
                contact.data = json.dumps(other_data, default=str)
                updated += 1
            else:
                new_contact = Contact(phone=clean_phone, data=json.dumps(other_data, default=str))
                db.session.add(new_contact)
                count += 1
        
        db.session.commit()
        flash(f'Imported {count} new contacts, updated {updated}.')
        return redirect(url_for('main.list_contacts'))
    except Exception as e:
        flash(f'Error saving: {str(e)}')
        return redirect(url_for('main.upload_contacts'))

@main_bp.route('/contacts/list')
@login_required
def list_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).limit(500).all()
    return render_template('contacts_list.html', contacts=contacts)

@main_bp.route('/contacts/delete/<int:id>', methods=['POST'])
@login_required
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('تم حذف الرقم بنجاح')
    return redirect(url_for('main.list_contacts'))

# --- Templates ---
@main_bp.route('/templates', methods=['GET', 'POST'])
@login_required
def templates():
    if request.method == 'POST':
        name = request.form.get('name')
        prov_id = request.form.get('provider_id')
        header_type = request.form.get('header_type')
        # Channel ID is now global, we ignore per-template input
        
        # Parse variable config logic (simplified for now)
        # Assuming user inputs how many vars they need
        body_vars_count = int(request.form.get('body_vars_count', 0))
        var_config = {
            "body_vars_count": body_vars_count
        }

        tmpl = Template(name=name, provider_template_id=prov_id, channel_id=None, 
                        header_type=header_type, variable_config=json.dumps(var_config))
        db.session.add(tmpl)
        db.session.commit()
        flash('Template added.')
        return redirect(url_for('main.templates'))
        
    templates = Template.query.all()
    return render_template('templates.html', templates=templates)

@main_bp.route('/templates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    tmpl = Template.query.get_or_404(id)
    
    if request.method == 'POST':
        tmpl.name = request.form.get('name')
        tmpl.provider_template_id = request.form.get('provider_id')
        tmpl.header_type = request.form.get('header_type')
        
        body_vars_count = int(request.form.get('body_vars_count', 0))
        var_config = {
            "body_vars_count": body_vars_count
        }
        tmpl.variable_config = json.dumps(var_config)
        
        db.session.commit()
        flash('تم تحديث القالب بنجاح')
        return redirect(url_for('main.templates'))
        
    # Parse config to pre-fill form
    config = json.loads(tmpl.variable_config)
    return render_template('edit_template.html', template=tmpl, config=config)

@main_bp.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
def delete_template(id):
    tmpl = Template.query.get_or_404(id)
    db.session.delete(tmpl)
    db.session.commit()
    flash('تم حذف القالب بنجاح')
    return redirect(url_for('main.templates'))

# --- Campaigns ---
@main_bp.route('/campaigns')
@login_required
def campaigns_list():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template('campaigns.html', campaigns=campaigns)

@main_bp.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        name = request.form.get('name')
        template_id = request.form.get('template_id')
        target_mode = request.form.get('target_mode') # all, manual
        
        # Check settings exist first
        settings = SystemSetting.query.first()
        if not settings or not settings.api_key:
            flash('Error: System settings (API Key) not configured. Please contact admin.')
            return redirect(url_for('main.create_campaign'))

        template = Template.query.get(template_id)
        
        # Handle Variables (Dynamic)
        body_vars = {}
        for key in request.form:
            if key.startswith('var_'):
                idx = key.split('_')[1]
                body_vars[idx] = request.form[key]

        header_file_path = None
        if template.header_type in ['image', 'video', 'document']:
            file = request.files.get('header_file')
            if file:
                filename = secure_filename(f"camp_{name}_{file.filename}")
                header_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(header_file_path)

        # Create Campaign
        camp = Campaign(name=name, template_id=template.id, status='pending')
        db.session.add(camp)
        db.session.commit()

        # Add Jobs
        jobs_count = 0
        if target_mode == 'all':
            contacts = Contact.query.all()
            for c in contacts:
                job = CampaignJob(campaign_id=camp.id, contact_id=c.id, phone_number=c.phone)
                db.session.add(job)
                jobs_count += 1
        elif target_mode == 'manual':
            manual_numbers = request.form.get('manual_numbers').split(',')
            for num in manual_numbers:
                if num.strip():
                    job = CampaignJob(campaign_id=camp.id, phone_number=num.strip())
                    db.session.add(job)
                    jobs_count += 1

        camp.total_contacts = jobs_count
        db.session.commit()

        # Trigger Task
        variable_mapping = {
            'body_vars': body_vars,
            'header_type': template.header_type,
            'header_file_path': header_file_path
        }
        # We don't pass api_key anymore, the task will fetch it from DB
        process_campaign.delay(camp.id, variable_mapping)

        flash('Campaign started!')
        return redirect(url_for('main.dashboard'))

    templates = Template.query.all()
    return render_template('create_campaign.html', templates=templates)

@main_bp.route('/campaigns/export_failed/<int:id>')
@login_required
def export_failed(id):
    campaign = Campaign.query.get_or_404(id)
    failed_jobs = CampaignJob.query.filter_by(campaign_id=id, status='failed').all()
    
    if not failed_jobs:
        flash('لا توجد أرقام فاشلة في هذه الحملة.')
        return redirect(url_for('main.campaigns_list'))
    
    # Create DataFrame
    data = []
    for job in failed_jobs:
        data.append({
            'Phone': job.phone_number,
            'Reason': job.response_log
        })
    
    df = pd.DataFrame(data)
    
    # Save to buffer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'failed_contacts_campaign_{id}.xlsx'
    )

@main_bp.route('/campaigns/retry/<int:id>', methods=['GET', 'POST'])
@login_required
def retry_campaign(id):
    original_camp = Campaign.query.get_or_404(id)
    # Fetch Failed AND Queued (Not Sent) jobs
    # This allows resuming a stopped campaign or retrying failed ones
    pending_jobs = CampaignJob.query.filter(
        CampaignJob.campaign_id == id,
        CampaignJob.status.in_(['failed', 'queued'])
    ).all()
    
    if not pending_jobs:
        flash('لا توجد أرقام فاشلة أو معلقة لإعادة المحاولة.')
        return redirect(url_for('main.campaigns_list'))

    if request.method == 'POST':
        # 1. Create New Campaign
        new_name = request.form.get('name')
        new_template_id = request.form.get('template_id')
        template = Template.query.get(new_template_id)
        
        new_camp = Campaign(name=new_name, template_id=template.id, status='pending')
        db.session.add(new_camp)
        db.session.commit()
        
        # 2. Copy Failed/Queued Jobs
        count = 0
        for old_job in pending_jobs:
            # We create new jobs for the new campaign
            new_job = CampaignJob(
                campaign_id=new_camp.id,
                contact_id=old_job.contact_id, 
                phone_number=old_job.phone_number,
                status='queued'
            )
            db.session.add(new_job)
            count += 1
        
        new_camp.total_contacts = count
        db.session.commit()
        
        # 3. Handle Variables & File
        body_vars = {}
        for key in request.form:
            if key.startswith('var_'):
                idx = key.split('_')[1]
                body_vars[idx] = request.form[key]

        header_file_path = None
        if template.header_type in ['image', 'video', 'document']:
            file = request.files.get('header_file')
            if file:
                filename = secure_filename(f"camp_{new_name}_{file.filename}")
                header_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(header_file_path)
        
        # 4. Launch Task
        variable_mapping = {
            'body_vars': body_vars,
            'header_type': template.header_type,
            'header_file_path': header_file_path
        }
        process_campaign.delay(new_camp.id, variable_mapping)
        
        flash(f'تم استئناف/إعادة الحملة لـ {count} رقم.')
        return redirect(url_for('main.dashboard'))

    templates = Template.query.all()
    return render_template('retry_campaign.html', campaign=original_camp, failed_count=len(pending_jobs), templates=templates)

# --- Settings & Admin ---
@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        flash('Access denied. Admins only.')
        return redirect(url_for('main.dashboard'))

    settings = SystemSetting.query.first()
    if not settings:
        settings = SystemSetting(api_key='', channel_id='', base_url='')
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.api_key = request.form.get('api_key')
        settings.channel_id = request.form.get('channel_id')
        settings.base_url = request.form.get('base_url')
        db.session.commit()
        flash('Settings updated successfully.')
        return redirect(url_for('main.settings'))

    return render_template('settings.html', settings=settings)

@main_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User created')
    
    users = User.query.all()
    return render_template('users.html', users=users)

# --- FESTIVAL PUBLIC PAGE ---

@main_bp.route('/festival', strict_slashes=False)
def public_festival():
    """ The public landing page """
    # Log Visit
    try:
        # Get Real IP behind Proxy
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        elif request.headers.get("X-Real-IP"):
            ip = request.headers.get("X-Real-IP")
        else:
            ip = request.remote_addr

        # Simple logging, avoiding spam checks for now
        visit = PageVisit(
            page_name='festival',
            ip_address=ip,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(visit)
        db.session.commit()
    except:
        pass # Don't crash site if logging fails

    settings = FestivalSettings.query.first()
    if not settings:
        settings = FestivalSettings() # Default
        db.session.add(settings)
        db.session.commit()
    
    images = FestivalImage.query.order_by(FestivalImage.created_at.desc()).all()
    return render_template('public_festival.html', settings=settings, images=images)

@main_bp.route('/settings/festival', methods=['GET', 'POST'])
@login_required
def manage_festival():
    # Admin check removed to allow all users to manage festival
    
    settings = FestivalSettings.query.first()
    if not settings:
        settings = FestivalSettings()
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        # Update Text
        if 'title' in request.form:
            settings.title = request.form.get('title')
            settings.description = request.form.get('description')
            db.session.commit()
            flash('تم تحديث النصوص بنجاح')
        
        # Upload New Image
        if 'new_image' in request.files:
            file = request.files.get('new_image')
            if file and file.filename:
                filename = secure_filename(str(datetime.now().timestamp()) + "_" + file.filename)
                upload_dir = os.path.join(current_app.root_path, 'static/uploads/festival')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                
                new_img = FestivalImage(filename=filename, caption=request.form.get('caption', ''))
                db.session.add(new_img)
                db.session.commit()
                flash('تم رفع الصورة')
                
        return redirect(url_for('main.manage_festival'))

    images = FestivalImage.query.order_by(FestivalImage.created_at.desc()).all()
    return render_template('manage_festival.html', settings=settings, images=images)

@main_bp.route('/settings/festival/delete/<int:id>', methods=['POST'])
@login_required
def delete_festival_image(id):
    img = FestivalImage.query.get_or_404(id)
    # Optional: Delete actual file
    try:
        file_path = os.path.join(current_app.root_path, 'static/uploads/festival', img.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass # Ignore file errors
    
    db.session.delete(img)
    db.session.commit()
    flash('تم حذف الصورة')
    return redirect(url_for('main.manage_festival'))
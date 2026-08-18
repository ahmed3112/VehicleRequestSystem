from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-in-production")
DB = Path(os.getenv("DB_PATH", str(Path(__file__).with_name("parking.db"))))
DB.parent.mkdir(parents=True, exist_ok=True)


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL UNIQUE,
        vehicle_type TEXT NOT NULL,
        brand TEXT DEFAULT '',
        model TEXT DEFAULT '',
        chassis_number TEXT DEFAULT '',
        engine_number TEXT DEFAULT '',
        manufacture_year INTEGER,
        line_id INTEGER,
        status TEXT NOT NULL DEFAULT 'Active',
        driver_name TEXT DEFAULT '',
        FOREIGN KEY(line_id) REFERENCES lines(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()

BASE = """
<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>نظام موقف العربيات</title><style>
body{font-family:Arial,sans-serif;background:#f4f6f8;margin:0;color:#17202a}nav{background:#17202a;color:white;padding:15px 5%;display:flex;gap:20px;align-items:center}nav a{color:white;text-decoration:none}.wrap{max-width:1200px;margin:25px auto;padding:0 18px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px}.card{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px #0001}.num{font-size:30px;font-weight:bold}.toolbar{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin:20px 0}input,select{padding:10px;border:1px solid #ccd3da;border-radius:7px;width:100%;box-sizing:border-box}button,.btn{background:#1769aa;color:white;border:0;border-radius:7px;padding:10px 15px;text-decoration:none;cursor:pointer}.btn.danger{background:#c62828}table{width:100%;border-collapse:collapse;background:white}th,td{padding:12px;border-bottom:1px solid #eee;text-align:right}th{background:#eef2f5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.field label{display:block;margin-bottom:6px;font-weight:bold}.field{margin-bottom:12px}.alert{padding:10px;background:#fff3cd;border-radius:7px;margin-bottom:15px}
</style></head><body><nav><strong>🚗 موقف العربيات</strong><a href='/'>الرئيسية</a><a href='/lines'>الخطوط</a><a href='/vehicles'>العربيات</a></nav><div class='wrap'>{% with messages=get_flashed_messages() %}{% for m in messages %}<div class='alert'>{{m}}</div>{% endfor %}{% endwith %}{{content|safe}}</div></body></html>
"""

def page(content, **ctx):
    return render_template_string(BASE, content=render_template_string(content, **ctx))

@app.route('/')
def dashboard():
    conn=db(); lines=conn.execute("SELECT COUNT(*) c FROM lines").fetchone()['c']; vehicles=conn.execute("SELECT COUNT(*) c FROM vehicles").fetchone()['c']; active=conn.execute("SELECT COUNT(*) c FROM vehicles WHERE status='Active'").fetchone()['c']; maint=conn.execute("SELECT COUNT(*) c FROM vehicles WHERE status='Maintenance'").fetchone()['c']; stats=conn.execute("SELECT l.code,l.name,COUNT(v.id) count FROM lines l LEFT JOIN vehicles v ON v.line_id=l.id GROUP BY l.id ORDER BY l.code").fetchall(); conn.close()
    return page("""<h1>Dashboard</h1><div class='cards'><div class='card'>إجمالي الخطوط<div class='num'>{{lines}}</div></div><div class='card'>إجمالي العربيات<div class='num'>{{vehicles}}</div></div><div class='card'>العربيات العاملة<div class='num'>{{active}}</div></div><div class='card'>العربيات في الصيانة<div class='num'>{{maint}}</div></div></div><h2>عدد العربيات لكل خط</h2><table><tr><th>الكود</th><th>الخط</th><th>عدد العربيات</th></tr>{% for x in stats %}<tr><td>{{x.code}}</td><td>{{x.name}}</td><td><strong>{{x.count}}</strong></td></tr>{% else %}<tr><td colspan='3'>لا توجد خطوط</td></tr>{% endfor %}</table>""",lines=lines,vehicles=vehicles,active=active,maint=maint,stats=stats)

@app.route('/lines', methods=['GET','POST'])
def lines():
    conn=db()
    if request.method=='POST':
        try:
            conn.execute("INSERT INTO lines(code,name,description,status) VALUES(?,?,?,?)",(request.form['code'].strip(),request.form['name'].strip(),request.form.get('description',''),request.form.get('status','Active'))); conn.commit(); flash('تم إضافة الخط بنجاح')
        except sqlite3.IntegrityError: flash('كود الخط موجود بالفعل')
        return redirect(url_for('lines'))
    rows=conn.execute("SELECT l.*,COUNT(v.id) vehicle_count FROM lines l LEFT JOIN vehicles v ON v.line_id=l.id GROUP BY l.id ORDER BY l.id DESC").fetchall(); conn.close()
    return page("""<h1>الخطوط</h1><form method='post' class='card'><h3>إضافة خط</h3><div class='grid'><div class='field'><label>كود الخط</label><input name='code' required placeholder='L-01'></div><div class='field'><label>اسم الخط</label><input name='name' required></div><div class='field'><label>الوصف</label><input name='description'></div><div class='field'><label>الحالة</label><select name='status'><option>Active</option><option>Inactive</option></select></div></div><button>إضافة</button></form><h2>قائمة الخطوط</h2><table><tr><th>الكود</th><th>الخط</th><th>عدد العربيات</th><th>الحالة</th><th>إجراء</th></tr>{% for x in rows %}<tr><td>{{x.code}}</td><td>{{x.name}}</td><td><strong>{{x.vehicle_count}}</strong></td><td>{{x.status}}</td><td><a class='btn danger' href='/lines/delete/{{x.id}}' onclick=\"return confirm('حذف الخط؟')\">حذف</a></td></tr>{% else %}<tr><td colspan='5'>لا توجد بيانات</td></tr>{% endfor %}</table>""",rows=rows)

@app.route('/lines/delete/<int:id>')
def delete_line(id):
    conn=db(); conn.execute('DELETE FROM lines WHERE id=?',(id,)); conn.commit(); conn.close(); flash('تم حذف الخط'); return redirect(url_for('lines'))

@app.route('/vehicles', methods=['GET','POST'])
def vehicles():
    conn=db()
    if request.method=='POST':
        try:
            conn.execute("INSERT INTO vehicles(plate_number,vehicle_type,brand,model,chassis_number,engine_number,manufacture_year,line_id,status,driver_name) VALUES(?,?,?,?,?,?,?,?,?,?)",(request.form['plate_number'].strip(),request.form['vehicle_type'],request.form.get('brand',''),request.form.get('model',''),request.form.get('chassis_number',''),request.form.get('engine_number',''),request.form.get('manufacture_year') or None,request.form.get('line_id') or None,request.form.get('status','Active'),request.form.get('driver_name',''))); conn.commit(); flash('تم إضافة العربية بنجاح')
        except sqlite3.IntegrityError: flash('رقم العربية موجود بالفعل')
        return redirect(url_for('vehicles'))
    q=request.args.get('q','').strip()
    if q: rows=conn.execute("SELECT v.*,l.code line_code,l.name line_name FROM vehicles v LEFT JOIN lines l ON l.id=v.line_id WHERE v.plate_number LIKE ? OR v.chassis_number LIKE ? OR v.engine_number LIKE ? OR v.vehicle_type LIKE ? OR l.name LIKE ? ORDER BY v.id DESC",tuple('%'+q+'%' for _ in range(5))).fetchall()
    else: rows=conn.execute("SELECT v.*,l.code line_code,l.name line_name FROM vehicles v LEFT JOIN lines l ON l.id=v.line_id ORDER BY v.id DESC").fetchall()
    line_rows=conn.execute("SELECT id,code,name FROM lines WHERE status='Active' ORDER BY code").fetchall(); conn.close()
    return page("""<h1>العربيات</h1><form method='get'><input name='q' value='{{q}}' placeholder='بحث برقم العربية / الشاسيه / الموتور / الخط'></form><form method='post' class='card'><h3>إضافة عربية</h3><div class='grid'><div class='field'><label>رقم العربية / اللوحة</label><input name='plate_number' required></div><div class='field'><label>نوع العربية</label><select name='vehicle_type'><option>Bus</option><option>Microbus</option><option>Pickup</option><option>Truck</option><option>Van</option><option>Sedan</option><option>Other</option></select></div><div class='field'><label>الماركة</label><input name='brand'></div><div class='field'><label>الموديل</label><input name='model'></div><div class='field'><label>رقم الشاسيه</label><input name='chassis_number'></div><div class='field'><label>رقم الموتور</label><input name='engine_number'></div><div class='field'><label>سنة الصنع</label><input type='number' name='manufacture_year'></div><div class='field'><label>الخط</label><select name='line_id'><option value=''>-- بدون خط --</option>{% for l in line_rows %}<option value='{{l.id}}'>{{l.code}} - {{l.name}}</option>{% endfor %}</select></div><div class='field'><label>الحالة</label><select name='status'><option>Active</option><option>Maintenance</option><option>Inactive</option></select></div><div class='field'><label>السائق</label><input name='driver_name'></div></div><button>إضافة العربية</button></form><h2>قائمة العربيات</h2><table><tr><th>اللوحة</th><th>النوع</th><th>الشاسيه</th><th>الموتور</th><th>الخط</th><th>الحالة</th><th>السائق</th><th>إجراء</th></tr>{% for x in rows %}<tr><td><strong>{{x.plate_number}}</strong></td><td>{{x.vehicle_type}}</td><td>{{x.chassis_number}}</td><td>{{x.engine_number}}</td><td>{{x.line_code or '-'}} {{x.line_name or ''}}</td><td>{{x.status}}</td><td>{{x.driver_name or '-'}}</td><td><a class='btn danger' href='/vehicles/delete/{{x.id}}' onclick=\"return confirm('حذف العربية؟')\">حذف</a></td></tr>{% else %}<tr><td colspan='8'>لا توجد بيانات</td></tr>{% endfor %}</table>""",rows=rows,line_rows=line_rows,q=q)

@app.route('/vehicles/delete/<int:id>')
def delete_vehicle(id):
    conn=db(); conn.execute('DELETE FROM vehicles WHERE id=?',(id,)); conn.commit(); conn.close(); flash('تم حذف العربية'); return redirect(url_for('vehicles'))

init_db()
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000, debug=True)

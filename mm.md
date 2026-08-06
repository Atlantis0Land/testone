إليك الكود كما طلبت، صفحة بسيطة بـ Flask بدون أي تعليقات في الكود.

هذه الثغرة تُعرف باسم **Broken Access Control** (فقدان التحكم في الوصول) و **IDOR** (الوصول المباشر غير الآمن للكائنات).

### الكود المصاب بالثغرة:

```python
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = 'super_secret_key'

secret_data = {
    "admin": "بيانات سرية جداً للمدير: أرباح الشركة 100 ألف",
    "user1": "بيانات المستخدم الأول",
    "user2": "بيانات المستخدم الثاني"
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('dashboard', user_id=username))

    return render_template_string('''
        <form method="post">
            <input type="text" name="username" placeholder="اسم المستخدم">
            <input type="submit" value="تسجيل الدخول">
        </form>
    ''')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    user_data = secret_data.get(user_id, "لا توجد بيانات")
    return f"<h1>مرحباً {user_id}</h1><p>البيانات: {user_data}</p>"

if __name__ == '__main__':
    app.run(debug=True)

```

**كيف تشرح الثغرة للمتدربين:**

1. إذا قمت بتشغيل الكود، ستظهر لك صفحة تسجيل الدخول (`/`).
2. يمكنك كتابة `user1` وسيتم توجيهك إلى `/dashboard/user1` لتشاهد البيانات.
3. **التجربة والاختراق:** افتح متصفحاً جديداً تماماً (Incognito) أو نافذة جديدة (حيث لا يوجد تسجيل دخول مسبق)، واكتب الرابط مباشرة: `[http://127.0.0.1:5000/dashboard/admin](http://127.0.0.1:5000/dashboard/admin)`.
4. **النتيجة:** سيتم عرض بيانات الـ Admin السرية فوراً **بدون المرور بصفحة تسجيل الدخول**. المشكلة هنا أن الرابط يقبل أي مدخل ولا يتحقق مما إذا كان الزائر قد سجل دخوله فعلاً أم لا.

---

### كيف نضيف الأمان (طريقة المعالجة):

لإصلاح هذه الثغرة، سنقوم بتعديل مسار `dashboard` فقط. يجب أن نتحقق من شيئين عبر الـ `session`:

1. هل المستخدم مسجل دخول أصلاً؟
2. هل المستخدم الذي طلب الرابط هو نفس المستخدم صاحب البيانات؟

**الكود الآمن:**

```python
from flask import Flask, request, redirect, url_for, render_template_string, session

app = Flask(__name__)
app.secret_key = 'super_secret_key'

secret_data = {
    "admin": "بيانات سرية جداً للمدير: أرباح الشركة 100 ألف",
    "user1": "بيانات المستخدم الأول",
    "user2": "بيانات المستخدم الثاني"
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('dashboard', user_id=username))

    return render_template_string('''
        <form method="post">
            <input type="text" name="username" placeholder="اسم المستخدم">
            <input type="submit" value="تسجيل الدخول">
        </form>
    ''')

@app.route('/dashboard/<user_id>')
def dashboard(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    if session['username'] != user_id:
        return "غير مصرح لك بمشاهدة بيانات مستخدم آخر", 403

    user_data = secret_data.get(user_id, "لا توجد بيانات")
    return f"<h1>مرحباً {user_id}</h1><p>البيانات: {user_data}</p>"

if __name__ == '__main__':
    app.run(debug=True)

```

**ما الذي أضفناه للحماية؟**
أضفنا شرطين (If Statements) في دالة `dashboard`:

* الشرط الأول (`'username' not in session`) يمنع أي شخص من فتح الرابط مباشرة بدون تسجيل دخول، وسيعيده فوراً لصفحة اللوج إن.
* الشرط الثاني (`session['username'] != user_id`) يمنع المستخدم العادي (مثلاً user1) من تغيير الرابط في المتصفح إلى `/dashboard/admin` لسرقة بيانات المدير.

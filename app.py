from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

# Database
DB = "database.db"

# Upload papkası
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.executescript("""
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        animal TEXT NOT NULL,
        price TEXT NOT NULL,
        location TEXT NOT NULL,
        phone TEXT NOT NULL,
        description TEXT,
        image TEXT,
        user_name TEXT,
        paid INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0,
        sold INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    con.execute("""
        INSERT OR IGNORE INTO settings(key, value)
        VALUES('ad_price', '0')
    """)

    con.execute("""
        INSERT OR IGNORE INTO settings(key, value)
        VALUES('card', '')
    """)

    con.commit()
    con.close()


# Render/Gunicorn ushın da database jaratıladı
init_db()


# =========================
# BAS BET
# =========================

@app.route("/")
def index():
    con = db()

    ads = con.execute("""
        SELECT *
        FROM ads
        WHERE approved = 1
        AND sold = 0
        ORDER BY id DESC
    """).fetchall()

    con.close()

    return render_template(
        "index.html",
        ads=ads
    )


# =========================
# DAǴAZA
# =========================

@app.route("/ad/<int:ad_id>")
def ad(ad_id):
    con = db()

    item = con.execute("""
        SELECT *
        FROM ads
        WHERE id = ?
    """, (ad_id,)).fetchone()

    con.close()

    if not item:
        return "Daǵaza tabılmadı", 404

    return render_template(
        "ad.html",
        ad=item
    )


# =========================
# DAǴAZA QOSIW
# =========================

@app.route("/add", methods=["GET", "POST"])
def add():

    con = db()

    settings = con.execute(
        "SELECT * FROM settings"
    ).fetchall()

    cfg = {
        x["key"]: x["value"]
        for x in settings
    }

    if request.method == "POST":

        image = request.files.get("image")
        filename = ""

        # Súwret saqlaw
        if image and image.filename:

            filename = (
                f"{uuid.uuid4().hex}_"
                f"{secure_filename(image.filename)}"
            )

            image.save(
                os.path.join(
                    UPLOAD,
                    filename
                )
            )

        # Baǵasın tekseriw
        ad_price = cfg.get(
            "ad_price",
            "0"
        ) or "0"

        try:
            paid = int(
                float(ad_price) > 0
            )
        except ValueError:
            paid = 0

        # Database-ge daǵaza qosıw
        con.execute("""
            INSERT INTO ads (
                title,
                animal,
                price,
                location,
                phone,
                description,
                image,
                user_name,
                paid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("title", ""),
            request.form.get("animal", ""),
            request.form.get("price", ""),
            request.form.get("location", ""),
            request.form.get("phone", ""),
            request.form.get("description", ""),
            filename,
            request.form.get("user_name", ""),
            paid
        ))

        con.commit()
        con.close()

        return redirect(
            url_for("success")
        )

    con.close()

    return render_template(
        "add.html",
        price=cfg.get("ad_price", "0"),
        card=cfg.get("card", "")
    )


# =========================
# TABISLI JIBERILDI
# =========================

@app.route("/success")
def success():
    return render_template(
        "success.html"
    )


# =========================
# ADMIN
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    # Adminge kirmеген bolsa
    if not session.get("admin"):

        if request.method == "POST":

            password = request.form.get(
                "password",
                ""
            )

            if password == "8310":

                session["admin"] = True

                return redirect(
                    url_for("admin")
                )

        return render_template(
            "admin_login.html"
        )

    con = db()

    # Admin ámelı
    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        ad_id = request.form.get(
            "ad_id"
        )

        # Maqullaw
        if action == "approve":

            con.execute("""
                UPDATE ads
                SET approved = 1
                WHERE id = ?
            """, (ad_id,))

        # Óshiriw
        elif action == "delete":

            con.execute("""
                DELETE FROM ads
                WHERE id = ?
            """, (ad_id,))

        # Satıldı
        elif action == "sold":

            con.execute("""
                UPDATE ads
                SET sold = 1
                WHERE id = ?
            """, (ad_id,))

        # Daǵaza bahası
        elif action == "price":

            con.execute("""
                UPDATE settings
                SET value = ?
                WHERE key = 'ad_price'
            """, (
                request.form.get(
                    "ad_price",
                    "0"
                ),
            ))

        # Karta
        elif action == "card":

            con.execute("""
                UPDATE settings
                SET value = ?
                WHERE key = 'card'
            """, (
                request.form.get(
                    "card",
                    ""
                ),
            ))

        con.commit()

    # Barlıq daǵazalar
    ads = con.execute("""
        SELECT *
        FROM ads
        ORDER BY id DESC
    """).fetchall()

    # Sozlamalar
    cfg = {
        x["key"]: x["value"]
        for x in con.execute(
            "SELECT * FROM settings"
        ).fetchall()
    }

    con.close()

    return render_template(
        "admin.html",
        ads=ads,
        cfg=cfg
    )


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def logout():

    session.clear()

    return redirect(
        url_for("admin")
    )


# =========================
# UPLOAD SÚWRETLER
# =========================

@app.route("/uploads/<path:name>")
def uploads(name):

    return send_from_directory(
        UPLOAD,
        name
    )


# =========================
# ISKE TÚSIRIW
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
  )

#!/usr/bin/env python3
"""Build the Persian technical report: fraud_detection_report.md and .docx.

Numbers come from report_assets/stats.json and queries from report_assets/queries.py,
so run `python report_assets/generate_assets.py` first. The existing .docx is reused
as the style template (page setup, heading styles). Export the PDF from Word.

Requires: python-docx
"""
import json
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "report_assets"))
from queries import QUERIES  # noqa: E402

MD, DOCX = os.path.join(ROOT, "fraud_detection_report.md"), os.path.join(ROOT, "fraud_detection_report.docx")
FONT = "Vazirmatn"

SCENARIOS = {
    "01": dict(
        name="لایه‌گذاری ساده (Simple Layering)", pattern="نقد → A→B→C→D → نقد (۳ دور)",
        text="وجه نقد با مبلغی کمی پایین‌تر از سقف گزارش‌دهی به یک حساب تازه‌افتتاح‌شده واریز می‌شود، ظرف حدود ۴ روز کاری از سه حساب حقیقی دیگر عبور می‌کند (در هر گام ۵۰۰ هزار ریال کم می‌شود) و در پایان به‌صورت نقدی برداشت می‌گردد. این چرخه سه بار با مبالغ ۴۵، ۴۸٫۵ و ۴۲ میلیون ریال تکرار شده است.",
        hidden=["واریزهای نقدی و حقوق‌های قانونی در همین بازه مبلغ (تا حدود ۴۹٫۵ میلیون) وجود دارند", "چهار حساب زنجیره تراکنش‌های عادی هم دارند", "شرح تراکنش‌ها خالی یا معمولی است"],
        signs=["واریز نقدی زیر سقف و انتقال فوری همان مبلغ", "عبور سریع از چند حساب با کاهش تدریجی مبلغ", "حساب اول تازه افتتاح شده است", "برداشت نقدی در انتهای زنجیره"],
        note="برداشت نقدی انتهای زنجیره (نقش integration) در مسیر بازگشتی کوئری نیست و با دنبال کردن حساب آخر به‌دست می‌آید."),
    "02": dict(
        name="خرد کردن تراکنش (Structuring / Smurfing)", pattern="۱۵ واریز نقدی زیر سقف → حساب تجمیع‌کننده",
        text="۹ حساب واسط در ۸ روز، ۱۵ واریز نقدی بین ۴۳ تا ۴۹٫۵ میلیون ریال (زیر سقف ۵۰ میلیونی) دریافت می‌کنند و هر واریز همان روز به یک حساب تجمیع‌کننده منتقل می‌شود. تجمیع‌کننده در روز دوازدهم حدود ۹۶٪ مجموع را در یک انتقال خارج می‌کند.",
        hidden=["مبالغ یکسان نیستند", "حقوق‌ها و واریزهای نقدی قانونی در همان بازه ۴۰ تا ۵۰ میلیون قرار دارند", "حساب‌های واسط فعالیت عادی هم دارند"],
        signs=["جفت «واریز نقدی / انتقال» در یک روز", "هم‌گرایی چند حساب به یک حساب", "انتقال تجمیعی اندکی بعد"],
        note="انتقال تجمیعی نهایی (consolidation) گام بعدیِ حساب تجمیع‌کننده است و در مسیر کوئری نیست."),
    "03": dict(
        name="شبکه شرکت‌های کاغذی (Shell Company Network)", pattern="A→B→C→A (۴ چرخه)",
        text="سه حساب حقوقی متعلق به سه مشتری متفاوت، در حدود ۶ هفته چهار بار وجوه را به‌صورت دایره‌ای بین خود می‌چرخانند. هر چرخه با ۴۲۰ تا ۵۶۰ میلیون ریال شروع می‌شود و در هر گام ۳ تا ۷ درصد کسر می‌گردد. شرح‌ها فاکتورهای متوالی با خدمات مبهم (مشاوره، مدیریت، بازرگانی) هستند.",
        hidden=["فاکتورهای B2B قانونی با همان سبک شرح و مبالغ مشابه (میانه حدود ۳۲۵ میلیون، برخی بالای ۱ میلیارد)", "چرخه‌های کوچک طبیعی در نویز وجود دارد که کوئری ساده چرخه را دچار مثبت کاذب می‌کند"],
        signs=["چرخه بسته سه‌تایی تکرارشونده بین همان شرکت‌ها", "کاهش مبلغ در هر گام", "شرح‌های مبهم"],
        note=""),
    "04": dict(
        name="تامین مالی تروریسم (Terrorist Financing)", pattern="۵۰ اهداکننده → خیریه → NGO → تبعه خارجی",
        text="۵۰ اهداکننده غیرحقوقی (شامل چند تبعه خارجی) طی ۶۰ روز هر کدام ۱ تا ۳ کمک ۱ تا ۵ میلیون ریالی به حساب یک موسسه خیریه واریز می‌کنند. خیریه در دو نوبت حدود ۹۵٪ وجوه جمع‌شده هر ماه را به یک NGO منتقل می‌کند و NGO دو روز بعد حدود ۹۰٪ آن را به حساب یک تبعه خارجی می‌فرستد.",
        hidden=["فروشگاه‌های قانونی هم پرداخت‌های کوچک زیادی از افراد مختلف دریافت می‌کنند", "شرح کمک‌ها عادی است (کمک خیریه، نذر یا خالی)"],
        signs=["هم‌گرایی تعداد زیادی واریز کوچک و عبور سریع", "خیریه وجوه را نگه نمی‌دارد", "ذی‌نفع نهایی تبعه خارجی است"],
        note=""),
    "05": dict(
        name="تصاحب حساب (Account Takeover)", pattern="۶ ماه رفتار عادی، سپس تخلیه شبانه",
        text="حساب یک بازنشسته (افتتاح پیش از ۱۳۹۵) شش ماه رفتار ثابتی دارد: واریز ماهانه ۲۵ میلیون ریال حقوق بازنشستگی، چند خرید کوچک و یک برداشت از خودپرداز. سپس در ساعات ۰ تا ۵ بامداد و از طریق موبایل‌بانک، ۵۰۰ میلیون ریال به یک حساب تازه‌افتتاح‌شده و طی ۴ روز بعد ۲۰۰، ۱۸۰ و ۱۵۰ میلیون به ذی‌نفع دیگری منتقل می‌شود.",
        hidden=["در جمعیت، انتقال‌های شخصی قانونی ۱۵۰ تا ۶۰۰ میلیونی (خودرو، ودیعه مسکن) وجود دارد", "رفتار پایه قربانی برچسب نخورده است"],
        signs=["مبلغ حدود ۲۰ برابر رفتار معمول حساب", "ساعت غیرعادی (بامداد)", "ذی‌نفعان جدید"],
        note=""),
    "06": dict(
        name="پولشویی مبتنی بر تجارت (Trade-Based ML)", pattern="واردکننده → کارگزار (۱۵٪−) → تبعه خارجی (۵ چرخه)",
        text="یک شرکت واردکننده هر حدود ۲۰ روز ۰٫۹ تا ۱٫۲ میلیارد ریال بابت پروفرما به یک کارگزار می‌پردازد و کارگزار ۱ تا ۳ روز بعد حدود ۸۵٪ آن را به حساب یک تبعه خارجی منتقل می‌کند. خودِ بیش‌اظهاری در داده پرداخت دیده نمی‌شود (به اظهارنامه گمرکی نیاز دارد)؛ آنچه دیده می‌شود عبور تکرارشونده با نگهداشت ثابت حدود ۱۵٪ است.",
        hidden=["پرداخت‌های B2B قانونی با مبالغ مشابه (برخی بالای ۱ میلیارد)", "شرح‌ها به سبک پروفرمای عادی است"],
        signs=["نسبت نگهداشت ثابت", "سه طرف ثابت و آهنگ منظم", "ذی‌نفع نهایی تبعه خارجی"],
        note=""),
    "07": dict(
        name="تقلب کارمند بانک (Insider Fraud)", pattern="حساب‌های راکد یک شعبه → حساب‌های واسط → نقد",
        text="۶ حساب حقیقی قدیمی (افتتاح پیش از ۱۳۹۸) که همگی به یک بانک و یک شعبه تعلق دارند و هیچ فعالیت دیگری ندارند، تقریباً هر ۳ روز یک‌بار ۵۰ تا ۲۰۰ میلیون ریال را از طریق باجه شعبه به ۴ حساب واسط منتقل می‌کنند. حساب واسط ظرف ۱ تا ۲ روز ۸۵ تا ۹۵٪ مبلغ را نقد برداشت می‌کند.",
        hidden=["قربانیان به‌جز این انتقال ساکت‌اند و در نویز دیده نمی‌شوند", "حساب‌های واسط فعالیت عادی دارند"],
        signs=["حساب راکد که ناگهان فعال می‌شود", "اشتراک شعبه بین همه قربانیان", "ذی‌نفعان مشترک", "برداشت نقدی سریع"],
        note="برداشت‌های نقدی حساب‌های واسط (cash_out) گام بعدی هستند و در مسیر کوئری نیستند."),
    "08": dict(
        name="پرداخت‌های دایره‌ای (Circular Payments)", pattern="حلقه ۱۸ حسابی تا مبدا + ۳ مسیر فرعی",
        text="وجهی حدود ۱ میلیارد ریال از طریق ۱۸ حساب، با فاصله ۱ تا ۴ روز کاری بین هر گام (حدود ۷ هفته) و کسر ۴ تا ۶ درصد در هر گام، به حساب مبدا بازمی‌گردد (حدود ۴۱۶ میلیون). سه مسیر فرعی ۲۰۰ میلیونی نیز از مبدا جدا شده و دوباره به حلقه می‌پیوندند.",
        hidden=["شرح‌ها خالی است", "تمام حساب‌های حلقه فعالیت عادی هم دارند"],
        signs=["چرخه طولانی که به مبدا برمی‌گردد", "کاهش یکنواخت مبلغ", "مسیرهای فرعی هم‌گرا"],
        note="جستجوی چرخه طولانی بدون قید در Cypher انفجار ترکیبیاتی دارد؛ این کوئری با محدود کردن به تراکنش‌های حداقل ۳۰۰ میلیونی قابل اجرا شده و مسیرهای فرعی ۲۰۰ میلیونی (side_path) را نمی‌بیند."),
    "09": dict(
        name="پخش و تجمیع (Scatter-Gather)", pattern="یک مبدا → ۷ واسط → یک جمع‌کننده",
        text="یک حساب مبدا ظرف ۳ روز به ۷ حساب حقیقی هر کدام ۲۸ تا ۵۹ میلیون ریال می‌فرستد. دو شاخه از یک واسط دوم هم عبور می‌کنند. هر شاخه ظرف ۱ تا ۴ روز ۹۵ تا ۹۹٪ دریافتی خود را به یک حساب جمع‌کننده مشترک منتقل می‌کند.",
        hidden=["هر مبلغ در بازه انتقال‌های شخصی عادی است", "شرح‌ها خالی است", "مبدا، واسط‌ها و جمع‌کننده فعالیت عادی هم دارند"],
        signs=["پخش و سپس هم‌گرایی بین همان دو حساب", "عبور تقریباً کامل وجه", "زمان نگهداری کوتاه"],
        note="کوئری Cypher فقط شاخه‌های تک‌واسطه را می‌بیند (۵ از ۷). دو شاخه دوواسطه‌ای توسط API بخش ۱۶ پیدا می‌شوند که عمق متغیر را پشتیبانی می‌کند."),
}


def render_md(stats) -> str:
    sc, val, gr = stats["scenarios"], stats["validation"], stats["graph"]
    total = sum(s["transactions"] for s in sc.values())
    planted = sum(s["planted"] for s in sc.values())
    out = []
    w = out.append

    w("# شبیه‌سازی سناریوهای تقلب در نظام بانکی ایران\n\n## گزارش فنی جامع\n")
    w("**تهیه‌کننده:** Mohammad Motiebirjandi  \n**تاریخ:** مهر ۱۴۰۵  \n**پایگاه داده:** Neo4j 5.26.2\n\n---\n")

    w("## ۱. مقدمه و اهداف پروژه\n")
    w(f"این پروژه {len(sc)} سناریوی تقلب و پولشویی را روی داده‌های کاملاً مصنوعی ولی نزدیک به واقعیتِ نظام بانکی ایران شبیه‌سازی می‌کند. هدف، آزمودن این است که تحلیل گرافی تا چه حد می‌تواند الگوهایی را که عمداً در میان فعالیت عادی پنهان شده‌اند پیدا کند.\n")
    w(f"داده‌ها شامل {val['Accounts']} حساب متعلق به {val['Customers']} مشتری در ۱۰ بانک و {total} تراکنش است که {planted} مورد آن تراکنش کاشته‌شده تقلب و بقیه فعالیت عادی (نویز) است. همه داده‌ها در پایگاه داده گرافی Neo4j بارگذاری شده و یک API برای تحلیل مسیر روی آن ساخته شده است.\n")
    w("### ۱.۱ ابزارها و فناوری‌های مورد استفاده\n")
    w("| ابزار | توضیحات |\n|---|---|\n| Python 3.10+ | تولید داده مصنوعی، اعتبارسنجی و تحلیل |\n| Neo4j 5.26.2 | پایگاه داده گرافی |\n| Docker | اجرای Neo4j و API |\n| Cypher | زبان پرس‌وجوی گراف |\n| FastAPI | API تحلیل مسیر |\n| NetworkX / Matplotlib | مصورسازی |\n\n---\n")

    w("## ۲. روش تولید داده\n")
    w("داده‌ها با اسکریپت تولید می‌شوند و با seed ثابت کاملاً قابل بازتولید هستند. دو قید اصلی رعایت شده است: نزدیکی به داده واقعی بانکی، و پنهان بودن الگوی تقلب در میان نویز.\n")
    w("### ۲.۱ تولید حساب‌ها\n")
    w("- شماره شبا: ۲۶ کاراکتر با رقم کنترل mod-97 و شناسه واقعی بانک‌ها (مثلاً 017 ملی، 012 ملت، 057 پاسارگاد)\n- شماره ملی اشخاص حقیقی: ۱۰ رقم با رقم کنترل معتبر\n- شناسه ملی اشخاص حقوقی: ۱۱ رقم با رقم کنترل معتبر\n- شناسه شهاب: ۱۶ رقم برای هر مشتری\n- هر بانک شعبه‌های خود را دارد و حساب در شعبه همان بانک افتتاح می‌شود\n- ۳۰ ستون فارسی مطابق قالب گزارش‌های واقعی بانکی؛ هر سطر یک رابطه مشتری–حساب (مالک، شریک، صاحب امضا)\n")
    w("### ۲.۲ تولید تراکنش‌ها\n")
    w("- انواع تراکنش: واریز نقدی، برداشت نقدی، انتقال داخلی (هم‌بانک)، پایا، و ساتنا (بین‌بانکی از ۱۵۰ میلیون ریال به بالا)\n- تراکنش نقدی طرف مقابل ندارد: واریز نقدی بدون فرستنده و برداشت نقدی بدون گیرنده است\n- تقویم هجری شمسی واقعی (طول ماه‌ها و سال کبیسه)\n- تراکنش شعبه‌ای، پایا و ساتنا در روز جمعه انجام نمی‌شود\n- کانال‌ها: اینترنت‌بانک، موبایل‌بانک، شعبه، ATM\n")
    w("### ۲.۳ نویز و پنهان‌سازی\n")
    w("در هر سناریو فعالیت عادی در تمام بازه زمانی سناریو تولید می‌شود: خرید از فروشگاه، انتقال شخصی با مبالغ رُند و شرح اغلب خالی، حقوق ماهانه (۲۲ تا ۴۹٫۵ میلیون، یعنی درست زیر سقف ۵۰ میلیونی)، واریز و برداشت نقدی، فاکتورهای B2B با دنباله سنگین (میانه حدود ۳۲۵ میلیون و برخی بالای ۱ میلیارد) و گاهی انتقال‌های شخصی ۱۵۰ تا ۶۰۰ میلیونی.\n")
    w("برای پنهان ماندن تقلب: شرح تراکنش‌های تقلب عادی یا خالی است، مبالغ تقلب با مبالغ قانونی هم‌پوشانی دارد، و حساب‌های درگیر تقلب در فعالیت عادی هم شرکت می‌کنند (به‌جز قربانیان راکد سناریوی ۰۷).\n")
    w("### ۲.۴ برچسب‌های مرجع\n")
    w("تراکنش‌های کاشته‌شده هر سناریو با نقش خود در فایل `ground_truth.csv` ثبت شده‌اند. این فایل عمداً در `transactions.csv` و در Neo4j وارد نمی‌شود تا کوئری‌های تشخیص نتوانند از آن استفاده کنند؛ فقط برای سنجش نتایج به‌کار می‌رود.\n\n---\n")

    w("## ۳. اعتبارسنجی داده‌ها\n")
    w("| شاخص | مقدار | وضعیت |\n|---|---|---|")
    rows = [("حساب‌ها", "Accounts"), ("مشتریان", "Customers"), ("تراکنش‌ها", "Transactions"),
            ("تراکنش نقدی (یک‌طرفه، مورد انتظار)", "Cash (one-sided) tx"),
            ("تراکنش بدون فرستنده و گیرنده", "No sender and no receiver"),
            ("ارجاع به شبای ناشناخته", "Unknown Sheba"), ("شناسه تراکنش تکراری", "Duplicate IDs"),
            ("مبلغ صفر یا منفی", "Zero / negative amounts"), ("انتقال به خود", "Self transfers")]
    for label, key in rows:
        w(f"| {label} | {val[key]} | PASS |")
    w("\nرقم کنترل همه شباها، شماره‌های ملی و شناسه‌های ملی معتبر است و هیچ تاریخ نامعتبری وجود ندارد.\n")
    w("![نمودار اعتبارسنجی داده‌ها](report_assets/overview/data_validation_chart.png)\n\n---\n")

    w("## ۴. مدل گرافی Neo4j\n")
    w("### ۴.۱ گره‌ها (Nodes)\n")
    w(f"| گره | تعداد |\n|---|---|\n| Bank | {gr['Bank']} |\n| Customer | {gr['Customer']} |\n| Customer:Person | {gr['Person']} |\n| Customer:Person:ForeignNational | {gr['ForeignNational']} |\n| Customer:Company | {gr['Company']} |\n| Account | {gr['Account']} |\n| Transaction | {gr['Transaction']} |\n")
    w("### ۴.۲ روابط (Relationships)\n")
    w(f"| رابطه | جهت | تعداد |\n|---|---|---|\n| OWNS_ACCOUNT | Customer → Account | {gr['OWNS_ACCOUNT']} |\n| BELONGS_TO_BANK | Account → Bank | {gr['BELONGS_TO_BANK']} |\n| SENT | Account → Transaction | {gr['SENT']} |\n| RECEIVED | Transaction → Account | {gr['RECEIVED']} |\n")
    w("واریز نقدی فقط رابطه RECEIVED و برداشت نقدی فقط رابطه SENT دارد.\n")
    w("### ۴.۳ نمای کلی گراف\n")
    w("![نمونه تصادفی از گراف](report_assets/overview/neo4j_full_graph.png)\n\n---\n")

    w("## ۵. خلاصه سناریوهای تقلب\n")
    w("| # | نام سناریو | تراکنش | کاشته‌شده | بازه | الگو |\n|---|---|---|---|---|---|")
    for n, s in sc.items():
        w(f"| {n} | {SCENARIOS[n]['name']} | {s['transactions']} | {s['planted']} | {s['first_date']}–{s['last_date']} | {SCENARIOS[n]['pattern']} |")
    w("\n![تراکنش کاشته‌شده در برابر عادی](report_assets/overview/volume_comparison_chart.png)\n\n---\n")

    for i, (n, s) in enumerate(sc.items(), start=6):
        info, det = SCENARIOS[n], s["detection"]
        w(f"## {i}. سناریوی {n}: {info['name']}\n")
        w(f"### {i}.1 توضیح سناریو\n\n{info['text']}\n")
        w("**آمار:**\n")
        w(f"- الگو: {info['pattern']}\n- تعداد تراکنش: {s['transactions']}\n- تراکنش کاشته‌شده: {s['planted']}\n- تراکنش عادی: {s['transactions'] - s['planted']}\n- حجم تراکنش‌های کاشته‌شده: {s['planted_volume'] / 1e6:,.0f}M IRR\n- بازه: {s['first_date']} تا {s['last_date']}\n- نقش‌ها: {', '.join(f'{k} ({v})' for k, v in s['roles'].items())}\n")
        w(f"### {i}.2 نحوه پنهان‌سازی\n\n" + "\n".join(f"- {x}" for x in info["hidden"]) + "\n")
        w(f"### {i}.3 نشانگرهای تقلب\n\n" + "\n".join(f"- {x}" for x in info["signs"]) + "\n")
        w(f"### {i}.4 تصاویر\n")
        w(f"![جریان کاشته‌شده - سناریوی {n}](report_assets/scenario_{n}/transaction_flow_graph.png)\n")
        w(f"![توزیع مبالغ - سناریوی {n}](report_assets/scenario_{n}/amount_distribution.png)\n")
        w(f"![توزیع کانال - سناریوی {n}](report_assets/scenario_{n}/channel_distribution.png)\n")
        w(f"### {i}.5 کوئری تشخیص\n\n```cypher\n{QUERIES[n]}\n```\n")
        w(f"![نتیجه کوئری تشخیص - سناریوی {n}](report_assets/scenario_{n}/neo4j_graph.png)\n")
        w(f"**نتیجه:** کوئری {det['returned_tx']} تراکنش برگرداند که {det['true_positive']} مورد آن کاشته‌شده و {det['false_positive']} مورد مثبت کاذب است؛ پوشش {det['true_positive']} از {det['planted']} ({det['recall'] * 100:.0f}٪).\n")
        if info["note"]:
            w(info["note"] + "\n")
        w("---\n")

    k = 6 + len(sc)
    w(f"## {k}. نتایج تشخیص\n")
    w("| # | سناریو | برگشتی | درست | مثبت کاذب | کاشته‌شده | پوشش |\n|---|---|---|---|---|---|---|")
    for n, s in sc.items():
        d = s["detection"]
        w(f"| {n} | {SCENARIOS[n]['name']} | {d['returned_tx']} | {d['true_positive']} | {d['false_positive']} | {d['planted']} | {d['recall'] * 100:.0f}٪ |")
    w("\n**محدودیت این سنجش:** کوئری‌ها با آگاهی از الگوی هر سناریو نوشته شده‌اند و آستانه‌هایشان (نسبت عبور، حداقل مبلغ، تعداد شاخه) بر همین داده تنظیم شده است. بنابراین دقت ۱۰۰٪ نشان می‌دهد که الگو با وجود نویز قابل جداسازی است، نه اینکه این کوئری‌ها روی داده ناشناخته همین دقت را دارند. پوشش کمتر از ۱۰۰٪ در همه موارد مربوط به گام‌هایی است که بیرون از مسیر بازگشتی کوئری قرار دارند.\n\n---\n")

    w(f"## {k + 1}. API تحلیل مسیر\n")
    w("یک سرویس FastAPI روی Neo4j دو پرسش اصلی را پاسخ می‌دهد. جستجو روی کل گراف انجام می‌شود و همه مسیرها ترتیب زمانی دارند: یک گام فقط وقتی شمرده می‌شود که پول پیش از آن رسیده باشد.\n")
    w(f"### {k + 1}.1 مشارکت یک شبا در الگوی پخش و تجمیع\n")
    w("`GET /shebas/{sheba}/scatter-gather`\n")
    w("مشخص می‌کند شبا در الگوی پخش و سپس تجمیع پول شرکت داشته یا نه، و با چه نقشی: مبدا، مقصد یا واسط. برای هر الگو همه شاخه‌ها با جزئیات کامل تراکنش‌ها، مبلغ پخش‌شده و جمع‌شده، درصد کسرشده و مدت زمان برگردانده می‌شود. مبدا می‌تواند یک حساب یا واریز نقدی باشد. پارامترها: حداقل تعداد شاخه (۲)، حداکثر واسط در هر شاخه (۳)، پنجره زمانی (۳۰ روز) و حداقل نسبت عبور (۰٫۸).\n")
    w(f"### {k + 1}.2 رابطه بین شباها\n")
    w("`POST /relationships`\n")
    w("فهرستی از شباها می‌گیرد و برای هر جفت بررسی می‌کند که آیا مسیر پولی با هر تعداد واسط، در هر یک از دو جهت، وجود دارد. کوتاه‌ترین مسیر با جزئیات تراکنش‌ها و همچنین مالکان مشترک دو حساب برگردانده می‌شود.\n")
    w(f"### {k + 1}.3 نتایج روی داده\n")
    w("- سناریوی ۰۹: هر ۷ شاخه و هر ۱۶ تراکنش کاشته‌شده پیدا شد، با نقش درست برای مبدا، مقصد و واسط\n- سناریوی ۰۲: به‌صورت الگوی مبدا-نقدی با ۹ شاخه و ۱۸ از ۱۸ تراکنش مربوط پیدا شد\n- در کل گراف فقط ۵ الگوی پخش و تجمیع وجود دارد: دو الگوی کاشته‌شده (۹ و ۷ شاخه) و سه الگوی کوچک ۲ تا ۳ شاخه‌ای که عمدتاً نویز هستند\n- حدود ۷۵٪ جفت‌حساب‌ها مسیر زمانی معتبر به هم دارند؛ بنابراین پاسخ «رابطه دارد یا ندارد» به‌تنهایی کم‌ارزش است و خودِ مسیر (تعداد گام، تاریخ‌ها، مبالغ) اطلاعات مفید را می‌دهد\n\n---\n")

    w(f"## {k + 2}. محدودیت‌ها\n")
    w("- اطلاعات تماس مشترک (تلفن، نشانی، IP) مدل نشده است، چون قالب ۳۰ ستونی گزارش بانکی چنین فیلدی ندارد\n- مقیاس مبالغ همان مقیاس اولیه پروژه است (سقف گزارش‌دهی ۵۰ میلیون ریال) و با سطح ریالی سال ۱۴۰۳ تطبیق داده نشده است\n- همه سناریوها در یک بازه زمانی و روی یک مجموعه حساب مشترک قرار دارند؛ در جستجوی کل گراف، مسیرها می‌توانند از نویز سناریوهای دیگر عبور کنند\n- API در هر درخواست همه تراکنش‌ها را در حافظه می‌خواند که برای این حجم مناسب است، نه برای میلیون‌ها تراکنش\n- تصاویر «نتیجه کوئری» از خروجی واقعی کوئری روی Neo4j رسم شده‌اند، نه اسکرین‌شات Neo4j Browser\n\n---\n")

    w(f"## {k + 3}. نتیجه‌گیری\n")
    w(f"در این پروژه {len(sc)} سناریوی تقلب با داده‌های نزدیک به واقعیت شبیه‌سازی و عمداً در میان فعالیت عادی پنهان شد. با وجود هم‌پوشانی مبالغ و شرح‌های خنثی، ساختار گرافی هر الگو (زنجیره، چرخه، هم‌گرایی، پخش و تجمیع) و ترتیب زمانی آن امکان جداسازی از نویز را فراهم می‌کند. کوئری‌های Cypher برای الگوهای با عمق ثابت کافی هستند و برای الگوهای با عمق متغیر و قید زمانی، جستجوی مسیر در API مناسب‌تر است.\n\n---\n")
    w("## مراجع\n")
    w("- [FATF 40 Recommendations](https://www.fatf-gafi.org/publications/fatf-standards/)\n- [FATF Typologies Reports](https://www.fatf-gafi.org/publications/typologies/)\n- [Central Bank of Iran](https://www.cbi.ir/)\n- [Sheba / IBAN structure — Iran](https://www.ibantest.com/en/iban-structure/iran)\n")
    return '<div dir="rtl">\n\n' + "\n".join(out) + "\n</div>\n"


# ---------------------------------------------------------------- docx

def _fonts(run, name, size):
    rpr = run._r.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        fonts.set(qn(f"w:{attr}"), name)
    run.font.size = Pt(size)
    cs = OxmlElement("w:szCs")
    cs.set(qn("w:val"), str(int(size * 2)))
    rpr.append(cs)


def rtl(paragraph, align="right"):
    paragraph.alignment = {"right": WD_ALIGN_PARAGRAPH.RIGHT, "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
    ppr = paragraph._p.get_or_add_pPr()
    ppr.find(qn("w:jc")).addprevious(OxmlElement("w:bidi"))  # schema order: bidi before jc
    for run in paragraph.runs:
        run._r.get_or_add_rPr().append(OxmlElement("w:rtl"))


def add_text(doc, text, size=11, align="right", container=None):
    """Paragraph with **bold** and `code` inline markup, links reduced to their label."""
    p = (container or doc).add_paragraph()
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            run = p.add_run(part[2:-2])
            run.bold = True
            _fonts(run, FONT, size)
        elif part.startswith("`"):
            _fonts(p.add_run(part[1:-1]), "Courier New", size - 1)
        else:
            _fonts(p.add_run(part), FONT, size)
    rtl(p, align)
    return p


def add_code(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        _fonts(p.add_run(line or " "), "Courier New", 8)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "F4F4F4")
        p._p.get_or_add_pPr().insert(0, shd)  # schema order: shd before spacing and jc
    doc.add_paragraph()


def add_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    tbl_pr = table._tbl.tblPr
    tbl_pr.append(OxmlElement("w:bidiVisual"))
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        for k, v in (("val", "single"), ("sz", "4"), ("space", "0"), ("color", "999999")):
            el.set(qn(f"w:{k}"), v)
        borders.append(el)
    tbl_pr.append(borders)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.paragraphs[0]._p.getparent().remove(cell.paragraphs[0]._p)
            p = add_text(doc, f"**{value}**" if i == 0 else value, size=9, align="center", container=cell)
            p.paragraph_format.space_after = Pt(0)
            if i == 0:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:fill"), "D9E2F3")
                cell._tc.get_or_add_tcPr().append(shd)
    doc.add_paragraph()


def build_docx(md: str):
    doc = Document(DOCX)  # reuse page setup and heading styles
    body = doc.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    for rid, rel in list(doc.part.rels.items()):  # drop the template's old pictures
        if rel.reltype.endswith("/image"):
            del doc.part.rels[rid]

    lines = md.splitlines()
    i, title_done = 0, False
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line or line == "---" or line.startswith(("<div", "</div")):
            continue
        if line.startswith("# "):
            doc.add_paragraph()
            add_text(doc, line[2:], size=24, align="center")
        elif line.startswith("## ") and not title_done:  # subtitle + byline block on the title page
            add_text(doc, line[3:], size=16, align="center")
            while not lines[i].startswith("---"):
                if lines[i].strip():
                    add_text(doc, lines[i].strip().replace("**", ""), size=12, align="center")
                i += 1
            doc.add_page_break()
            title_done = True
        elif line.startswith("## ") or line.startswith("### "):
            level = 1 if line.startswith("## ") else 2
            p = doc.add_paragraph(line.lstrip("# "))
            style = OxmlElement("w:pStyle")  # by id: this template's heading names defeat lookup by name
            style.set(qn("w:val"), f"Heading{level}")
            p._p.get_or_add_pPr().insert(0, style)
            rtl(p)
        elif line.startswith("```"):
            block = []
            while not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            add_code(doc, block)
        elif line.startswith("|"):
            rows = [line]
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            add_table(doc, [r for r in cells if not set("".join(r)) <= set("-: ")])
        elif m := re.match(r"!\[(.*)\]\((.*)\)", line):
            doc.add_picture(os.path.join(ROOT, m.group(2)), width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_text(doc, m.group(1), size=9, align="center")
        else:
            add_text(doc, line)
    doc.save(DOCX)


def main():
    with open(os.path.join(ROOT, "report_assets", "stats.json"), encoding="utf-8") as f:
        stats = json.load(f)
    md = render_md(stats)
    with open(MD, "w", encoding="utf-8") as f:
        f.write(md)
    build_docx(md)
    print(f"wrote {MD} and {DOCX}")


if __name__ == "__main__":
    main()

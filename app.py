import cv2
import numpy as np

def grade_paper(image_path):
    # 1. تحميل الصورة
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    # 2. البحث عن الدوائر (هنا يتم البحث عن الكنتورز)
    # ملاحظة: هذا الكود يحتاج لورقة مصممة خصيصاً ليتمكن من ترتيب الدوائر
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # منطق التصحيح (مثال مبسط جداً)
    score = 0
    answer_key = {0: 1, 1: 3, 2: 0} # السؤال 0 إجابته الخيار 1، وهكذا

    # في البرنامج الكامل، نقوم هنا بترتيب الدوائر وحساب عدد البكسلات السوداء داخل كل دائرة
    # الإجابة التي تحتوي على أقل عدد من البكسلات البيضاء (الأكثر تظليلاً) هي المختارة.
    
    print(f"تمت عملية المعالجة. النتيجة التقريبية: {score}")

# تشغيل الدالة
# grade_paper('path_to_your_image.jpg')
import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform

def process_exam(image_path):
    # 1. تحميل الصورة وتحويلها لرمادي
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    # 2. البحث عن إطار الورقة (أكبر مستطيل)
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    doc_cnt = None

    if len(cnts) > 0:
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                doc_cnt = approx
                break

    # 3. قص الورقة وتعديل منظورها
    paper = four_point_transform(image, doc_cnt.reshape(4, 2))
    warped = four_point_transform(gray, doc_cnt.reshape(4, 2))

    # 4. تحويل الصورة إلى أسود وأبيض بالكامل (Thresholding)
    thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    return thresh

# تشغيل البرنامج
# result = process_exam("exam_photo.jpg")
# cv2.imshow("Processed", result)
# cv2.waitKey(0)

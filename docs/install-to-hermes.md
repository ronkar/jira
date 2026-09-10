# טעינת המיומנויות לסוכן Hermes חדש

מדריך זה מסביר איך לגרום לסוכן **Hermes חדש** להכיר את כל מה שלמדנו על Jira Cloud,
כך שתוכל לבקש ממנו "תקים פרויקט Jira" והוא ידע בדיוק מה לעשות.

---

## מה צריך להתקין

שלוש מיומנויות (Skills) מתוך ה-repo הזה:

| תיקייה ב-repo | תפקיד |
|----------------|-------|
| `skills/jira-cloud-boards/` | ביצוע טכני: יצירת boards/workflows/סטטוסים + פיצול עמודות (greenhopper) |
| `skills/jira-dynamic-workflow/` | תפקיד הסוכן: ניתוח צורך → הצעה → אישור → ביצוע → דיווח |
| `skills/jira-cloud-api/` | אוטומציה כללית של Jira REST |

---

## שיטה 1 — העתקה ידנית (הפשוטה והמומלצת)

מיומנויות Hermes חיות בתיקייה:
```
~/.hermes/skills/<category>/<skill-name>/SKILL.md
```

העתק את שלוש התיקיות מהריפו לתוך תיקיית המיומנויות של הסוכן החדש:

```bash
# מתוך העותק המקומי של הריפו
cd /path/to/jira-repo

# צור את התיקיות והעתק
mkdir -p ~/.hermes/skills/productivity
cp -r skills/jira-cloud-boards   ~/.hermes/skills/productivity/
cp -r skills/jira-dynamic-workflow ~/.hermes/skills/productivity/
cp -r skills/jira-cloud-api      ~/.hermes/skills/productivity/

# העתק גם את הסקריפטים (הם חלק מהמיומנות jira-cloud-boards)
cp -r scripts/* ~/.hermes/skills/productivity/jira-cloud-boards/scripts/ 2>/dev/null
```

**אימות שהמיומנויות נטענו:** בסוכן החדש, בקש:
```
רשימת מיומנויות
```
או הרץ `hermes skills list` — אמורות להופיע `jira-cloud-boards`, `jira-dynamic-workflow`, `jira-cloud-api`.

---

## שיטה 2 — הורדה ישירות מ-GitHub (ללא העתקה מקומית)

```bash
git clone https://github.com/ronkar/jira.git /tmp/jira-skills
mkdir -p ~/.hermes/skills/productivity
cp -r /tmp/jira-skills/skills/* ~/.hermes/skills/productivity/
cp -r /tmp/jira-skills/scripts/* ~/.hermes/skills/productivity/jira-cloud-boards/scripts/ 2>/dev/null
```

---

## שלב חובה — הגדרת פרטי התחברות (Credentials)

הסקריפטים קוראים את פרטי ההתחברות מקובץ:
```
/root/jira_cloud/credentials.env
```

צור את הקובץ הזה על המכונה של הסוכן החדש עם התוכן הבא:

```bash
JIRA_BASE=https://ronkarny5547.atlassian.net
JIRA_EMAIL=<האימייל שלך>
JIRA_TOKEN=<ה-API token שלך>
JIRA_LEAD=<accountId שלך>   # אופציונלי — lead של פרויקטים חדשים
```

הגן על הקובץ:
```bash
chmod 600 /root/jira_cloud/credentials.env
```

> **חשוב:** ה-API token נוצר ב-https://id.atlassian.com/manage-profile/security/api-tokens
> וזהו **Basic auth** (אימייל + token) — לא סיסמה רגילה.

---

## בדיקה מהירה שהכל עובד

בסוכן החדש, בקש בדיקה פשוטה:
```
תראה לי את כל הפרויקטים ב-Jira
```
אם הוא מחזיר את רשימת הפרויקטים (AG, REL, SUP, TASK, TEAM...) — ההתקנה הצליחה.

או הרץ ישירות את הסקריפט:
```bash
python3 ~/.hermes/skills/productivity/jira-cloud-boards/scripts/setup_team_board.py --help
```

---

## איך הסוכן החדש ישתמש בזה

כשתבקש משהו כמו:
> "יש לי פרויקט ניתוח דאטה שאני רוצה להקים"

הסוכן יטען את מיומנות `jira-dynamic-workflow`, יבצע:
1. ניתוח התחום והתפקידים
2. הצעת מבנה workflow
3. **בקשת אישור ממך**
4. ביצוע טכני (פרויקט + workflow + board עם `location`)
5. **פיצול עמודות אוטומטי** (greenhopper)
6. דיווח עם קישור ל-board

---

## פתרון בעיות

| בעיה | פתרון |
|------|--------|
| "Skill not found" | ודא שהתיקייה נמצאת תחת `~/.hermes/skills/<category>/<name>/SKILL.md` |
| 401 Unauthorized | בדוק את `credentials.env` — אימייל + token נכונים |
| board לא נטען בממשק | כנראה נוצר בלי `location` — מחק וצור מחדש עם `location` |
| עמודות לא מתפצלות | הרץ `set_columns.py` ואמת ע"י re-GET (לא להסתפק ב-200) |

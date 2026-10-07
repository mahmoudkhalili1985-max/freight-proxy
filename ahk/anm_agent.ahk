; ═══════════════════════════════════════════════════════════════
; ANM Agent v2 — اتصال به سرور Render
; ═══════════════════════════════════════════════════════════════
#Requires AutoHotkey v2.0
#SingleInstance Force

; ─── تنظیمات — آدرس سرور Render خود را اینجا وارد کنید ───────
SERVER_URL := "https://freight-system.onrender.com"  ; <-- تغییر دهید
POLL_MS    := 3000
ANM_TITLE  := "ANM"

global coords := Map()
LoadCoords()

; ─── GUI ────────────────────────────────────────────────────────
g := Gui("+AlwaysOnTop", "ANM Agent")
g.SetFont("s9", "Tahoma")
g.Add("Text",, "Server:")
serverEdit := g.Add("Edit", "w240", SERVER_URL)
g.Add("Button", "w240", "ذخیره آدرس").OnEvent("Click", SaveServer)
g.Add("Text",, "───────────────────────")
g.Add("Text",, "وضعیت:")
statusTxt := g.Add("Text", "w240 c0x0066cc", "آماده")
g.Add("Text",, "───────────────────────")
g.Add("Text",, "تنظیم مختصات ANM:")
g.Add("Button", "w240", "1 - فیلد اول (سریال/سفارش)").OnEvent("Click", (*) => Capture("f1"))
g.Add("Button", "w240", "2 - فیلد دوم (مقصد/حواله)").OnEvent("Click", (*) => Capture("f2"))
g.Add("Button", "w240", "3 - فیلد تعداد در نوار ابزار").OnEvent("Click", (*) => Capture("f3"))
g.Add("Button", "w240", "4 - دکمه پرینتر").OnEvent("Click", (*) => Capture("f4"))
g.Add("Button", "w240", "5 - دکمه OK تایید").OnEvent("Click", (*) => Capture("f5"))
g.Add("Text",, "───────────────────────")
startBtn := g.Add("Button", "w240", "▶  شروع")
startBtn.OnEvent("Click", StartPoll)
stopBtn  := g.Add("Button", "w240", "■  توقف")
stopBtn.OnEvent("Click", StopPoll)
g.Show("x10 y10 w260")

; ─── Polling ─────────────────────────────────────────────────────
global active := false

SaveServer(*) {
    global SERVER_URL
    SERVER_URL := Trim(serverEdit.Value)
    IniWrite(SERVER_URL, A_ScriptDir "\anm_coords.ini", "Settings", "server")
    Status("آدرس ذخیره شد")
}

StartPoll(*) {
    global active
    active := true
    SetTimer(Poll, POLL_MS)
    Status("در حال بررسی سرور...")
}

StopPoll(*) {
    global active
    active := false
    SetTimer(Poll, 0)
    Status("متوقف شد")
}

Poll() {
    if !active
        return
    try {
        http := ComObject("WinHttp.WinHttpRequest.5.1")
        http.Open("GET", SERVER_URL "/api/print-queue", false)
        http.SetTimeouts(5000, 5000, 10000, 10000)
        http.Send()
        if http.Status != 200
            return
        resp := http.ResponseText
        if InStr(resp, '"pending"') {
            Status("دریافت دستور چاپ...")
            RunJobs(resp)
        }
    } catch as e {
        Status("خطا: " SubStr(e.Message, 1, 40))
    }
}

RunJobs(jsonText) {
    ; استخراج ساده mill از JSON
    mill := "arfeh"
    if InStr(jsonText, '"chadormaloo"')
        mill := "chadormaloo"

    ; استخراج jobs array — برای هر job جداگانه پردازش می‌کنیم
    ; از ScriptControl برای parse JSON استفاده می‌کنیم
    try {
        sc := ComObject("ScriptControl")
        sc.Language := "JScript"
        sc.ExecuteStatement("var d=" jsonText)
        cnt := sc.Eval("d.jobs.length")

        loop cnt {
            i := A_Index - 1
            jmill := sc.Eval("d.jobs[" i "].mill")
            if jmill = "arfeh"
                DoArfeh(sc, i)
            else
                DoChadormaloo(sc, i)
            Sleep(2000)
        }
        Status("تمام دستورات اجرا شد")
    } catch as e {
        Status("خطا در پردازش: " SubStr(e.Message,1,50))
    }
}

DoArfeh(sc, i) {
    order := sc.Eval("d.jobs[" i "].order_number")
    waybill := sc.Eval("d.jobs[" i "].waybill_start")
    cnt := sc.Eval("d.jobs[" i "].count")
    Status("ارفع: " order " — " cnt " برگه")

    if !Activate()
        return
    TypeIn("f1", order)
    TypeIn("f2", waybill)
    TypeIn("f3", String(cnt))
    ClickCoord("f4")
    Sleep(1500)
    ClickCoord("f5")
}

DoChadormaloo(sc, i) {
    permit  := sc.Eval("d.jobs[" i "].permit_start")
    order4  := sc.Eval("d.jobs[" i "].delivery_order_short")
    dest    := sc.Eval("d.jobs[" i "].destination")
    cnt     := sc.Eval("d.jobs[" i "].count")
    restr   := sc.Eval("d.jobs[" i "].tonnage_restricted")
    field2  := dest " " order4
    if restr = "true" || restr = True
        field2 .= " *"
    Status("چادرملو: " order4 " — " cnt " برگه")

    if !Activate()
        return
    TypeIn("f1", permit)
    TypeIn("f2", field2)
    TypeIn("f3", String(cnt))
    ClickCoord("f4")
    Sleep(1500)
    ClickCoord("f5")
}

; ─── توابع کمکی ──────────────────────────────────────────────────
Activate() {
    if !WinExist(ANM_TITLE) {
        MsgBox("ANM باز نیست!", "خطا", 16)
        return false
    }
    WinActivate(ANM_TITLE)
    Sleep(400)
    return true
}

TypeIn(field, val) {
    ClickCoord(field)
    Sleep(150)
    Send("^a")
    Sleep(80)
    Send(val)
    Sleep(200)
}

ClickCoord(name) {
    if !coords.Has(name) {
        MsgBox("مختصات " name " تنظیم نشده!", "خطا", 16)
        return
    }
    c := coords[name]
    Click(c[1] " " c[2])
    Sleep(100)
}

Capture(name) {
    MsgBox("3 ثانیه وقت دارید روی فیلد " name " در ANM کلیک کنید", "تنظیم", 64)
    Sleep(3000)
    MouseGetPos(&x, &y)
    coords[name] := [x, y]
    SaveCoords()
    Status(name " = " x "," y " ذخیره شد")
}

SaveCoords() {
    f := A_ScriptDir "\anm_coords.ini"
    for name, c in coords
        IniWrite(c[1] "," c[2], f, "Coords", name)
}

LoadCoords() {
    f := A_ScriptDir "\anm_coords.ini"
    if !FileExist(f)
        return
    global SERVER_URL
    try { SERVER_URL := IniRead(f, "Settings", "server") } catch {}
    for _, name in ["f1","f2","f3","f4","f5"] {
        try {
            val := IniRead(f, "Coords", name)
            parts := StrSplit(val, ",")
            if parts.Length = 2
                coords[name] := [Integer(parts[1]), Integer(parts[2])]
        } catch {}
    }
}

Status(msg) => statusTxt.Value := msg

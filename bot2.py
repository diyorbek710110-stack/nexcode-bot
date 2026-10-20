import asyncio
import time
import random
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

API_ID = 31377078
API_HASH = "2f0e5b622252e0696381349aaa0847bd"

app = Client(
    "user_utag_session",
    api_id=API_ID,
    api_hash=API_HASH
)

# So'zlar va emojilar ro'yxati
RANDOM_SOZLAR = [
    "Bir kirib chiqing, sizni kutishyapti 👀",
    "Qayerlarda yuribsiz, GPS ham topolmayapti 🛰️",
    "Chat sizni ko‘rmay ancha zerikdi 🥱",
    "Bir dona salom tashlab keting 👋",
    "Siz yo‘q paytda chat ham jim 🤐",
    "Kirib qo‘ying, hech kim tishlamaydi 😄",
    "Bir ko‘rinib, keyin yana g‘oyib bo‘ling 🫥",
    "Sizdan xabar kutyapmiz 📩",
    "Chatga tashrif buyurish vaqti keldi ⏰",
    "Qani, qayerdasizlar o‘zi? 🤨",
    "Bir gap yozing, ovozingizni eshitaylik 🎙️",
    "Sizsiz bu chatning fayzi yo‘q ✨",
    "Kirib qo‘ying, gaplar qizib ketdi 🔥",
    "Bir daqiqaga bo‘lsa ham ko‘rining 👁️",
    "Yo‘qolganlar ro‘yxatiga tushib qoldingiz 📋",
    "Sizni qidirib chatni aylanib chiqdik 🕵️‍♂️",
    "Bir xabar yozsangiz, kayfiyat ko‘tariladi 🎉",
    "Chat sizni sog‘inib qoldi 🤝",
    "Qani, aktivlikni ko‘rsating 📊",
    "Sizga ham navbat yetib keldi 🎯",
    "Bir kirib chiqing, yo‘l puli bizdan 🚌",
    "Chatga jon kiritadigan odam kerak ⚡",
    "Sizni ko‘rmaganimizga bir asr bo‘ldi 🗿",
    "Qayerga g‘oyib bo‘ldingiz? 🧭",
    "Bir og‘iz gap yozib qo‘ying 📝",
    "Siz bo‘lmasangiz chat yetim 🍂",
    "Kiravering, bahonani keyin topamiz 🤷‍♂️",
    "Chatga kirish uchun ruxsat berildi ✅",
    "Sizni kutishdan charchadik ⌛",
    "Bir dona xabar — shuncha qiyinmi? 🤯",
    "Qani endi bir ko‘rinsangiz 👀",
    "Chat jim, siz ham jim… bu nima holat 🤐",
    "Sizni chaqirishyapti, eshitmayapsizmi? 📢",
    "Bir kirib, kayfiyatni ko‘tarib keting 🌚",
    "Sizdan darak yo‘q, tergov boshlanadi 🔍",
    "Chatga tashrifingizni kutamiz 🚪",
    "Bir salom — bizga yetadi 👋",
    "Sizni online ko‘rish ham bayram 🎊",
    "Qani, bitta xabar tashlang 📨",
    "Chat sizni kutib turibdi 🪑",
    "Bugun ham g‘oyib bo‘lish rejangiz bormi? 🫥",
    "Bir ko‘rinib keting, begona bo‘lib ketmang 🙃",
    "Sizni unutib qo‘ymaylik deb chaqiryapmiz 📣",
    "Kirib qo‘ying, sizga joy bor 🪑",
    "Chatda siz uchun maxsus joy saqlangan 🎟️",
    "Biror narsa yozing, jimlikni buzaylik 🔊",
    "Sizsiz suhbatning yarmi yo‘q 🧩",
    "Qani, aktivlar safida ko‘rinish bering 📡",
    "Sizni kutyapmiz, bahona qabul qilinmaydi 🚫",
    "Bir daqiqaga kiring, chiqishingizga kafolat yo‘q 🚨",
    "Chatga kiring, qolganini o‘ylab ko‘ramiz 🤔",
    "Sizni online ko‘rish orzuga aylandi ✨",
    "Bir xabar yozing, keyin xohlasangiz g‘oyib bo‘ling 🫥",
    "Bugun sizning navbatingiz 🎯",
    "Chat sizni chaqiryapti 📢",
    "Qayerdasiz, osmonga chiqib ketmadingizmi? ☁️",
    "Bir kirib chiqing, hech narsa bo‘lmaydi 😌",
    "Sizni kutib chat qarib ketyapti 👴",
    "Biror gap bormi? Bo‘lmasa ham yozing 📝",
    "Siz kelmasangiz majlis boshlanmaydi 🏛️",
    "Chatning eshigi ochiq, marhamat 🚪",
    "Sizni ko‘rish uchun bahona izlayapmiz 🔎",
    "Bir salom tashlang, kunimiz yaxshi o‘tadi 🌤️",
    "G‘oyib bo‘lish bo‘yicha rekord yangilanmoqda 🏆",
    "Sizni topish qiyinlashib ketdi 🧭",
    "Chatga qaytish vaqti keldi 🔔",
    "Bir xabar bilan tarix yaratishingiz mumkin 📜",
    "Siz ham odamlar qatorida ko‘rining 👤",
    "Jimlikni siz buzishingiz kerak 🔥",
    "Chat sizsiz ishlamayapti deb bahona qilyapmiz 🛠️",
    "Bir kirib, hol-ahvol so‘rab chiqing 🙂",
    "Sizni chaqirish uchun signal yubordik 📡",
    "Online bo‘ling, yo‘qsa shubhali 🧐",
    "Bir dona emoji bo‘lsa ham tashlang 🙂",
    "Sizdan bir xabar kutib o‘tiribmiz 🕐",
    "Qani, bugungi ko‘rinishingizni kutamiz 👀",
    "Sizni ko‘rmasak kunimiz o‘tmaydi 🌙",
    "Chatga kirib, kayfiyatni ko‘tarib keting ✨",
    "Biror bahona bilan bo‘lsa ham kiring 🤷",
    "Sizni kutish ham bir san’at 🎨",
    "Bir ko‘rining, keyin yana yo‘qoling 🫥",
    "Chatda sizning ovozingiz yetishmayapti 🎧",
    "Qani, kim uyg‘oq? 🥱",
    "Siz ham biror narsa deb qo‘ying 🗣️",
    "Bugun chatga tashrif buyurish shart 📌",
    "Bir kirib chiqing, keyin o‘zingiz bilasiz 😌",
    "Sizni kutib turibmiz, kechikmang ⏳",
    "Chatning kayfiyati sizga bog‘liq 🎭",
    "Bir dona xabar tashlang, tamom 📨",
    "Yo‘qolgan odam topildi… yo‘q, hali ham yo‘q 🔍",
    "Sizga maxsus chaqiruv yuborildi 📩",
    "Kirib qo‘ying, gaplar bor 🤫",
    "Sizsiz chat juda sokin bo‘lib qoldi 🌙",
    "Qani, bir ko‘rinish bering 😎",
    "Bugun ham jim turmoqchimisiz? 🤐",
    "Chatga kirish bepul, imkoniyatdan foydalaning 🎁",
    "Sizni ko‘rmaganimizga ancha bo‘ldi 🕰️",
    "Bir salom yozing, qolganini biz qilamiz 🫡",
    "Qayerda bo‘lsangiz ham, chat sizni kutyapti 📍",
    "Bir kirib chiqing, keyin yana ishlaringizga qaytasiz 😅",
    "Sizdan xabar kelishini kutib turibmiz 📱",
    "Chatda sizning o‘rningiz bilinib turibdi 🧩",
    "Biror iz qoldirib keting 👣",
    "Sizni ko‘rish uchun bildirishnoma ham yubordik 🔔",
    "Qani, chatga bir nazar tashlang 👁️",
    "Sukutni buzadigan odam topilmadi 🤐",
    "Bir xabar yozib, g‘oyib bo‘lish mumkin 🫡",
    "Sizni kutayotganlar bor 📢",
    "Bugun ham online bo‘lish nasib qilsin 📶",
    "Bir ko‘rinib qo‘ying, keyin bemalol yo‘qoling 😴",
    "Chatga kirish eshigi ochiq 🚪",
    "Sizning xabaringiz yetishmayapti 📨",
    "Biror gap yozing, zerikib ketdik 🥱",
    "Sizni chaqirishning yana qanday usuli bor? 🤔",
    "Chatda jimlik darajasi rekordda 📉",
    "Bir dona xabar bilan vaziyatni o‘zgartiring ⚡",
    "Siz ham shu yerda ekaningizni isbotlang 🧐",
    "Bir salom tashlab, ishlaringizga qayting 👋",
    "Sizni kutib turish rejimi yoqildi 🔄",
    "Qani, aktivlikni biroz oshiramiz 📈",
    "Bugun chatga kirmaslik rejangiz bormi? 🗓️",
    "Sizning online holatingizni kutyapmiz 📶",
    "Bir ko‘rinib keting, xavotirga tushdik 🫡",
    "Chatga tashrif buyurish vaqti allaqachon kelgan ⏰",
    "Bir xabar yozing, keyin jimlik davom etadi 🤫",
    "Sizni chaqirdik, endi navbat sizda 📢",
    "Qayerga yashirindingiz? 🧐",
    "Biror narsa deb qo‘ying, bo‘lmasa o‘zimiz gaplashamiz 🗣️",
    "Siz yo‘q paytda yangi rekord o‘rnatdik 🏆",
    "Chatga qaytish uchun eng yaxshi vaqt — hozir ⏱️",
    "Bir kirib chiqing, ko‘nglimiz joyiga tushadi 🙂",
    "Sizni ko‘rish uchun kutish rejimi yoqilgan 🔋",
    "Chat sizning xabaringizni kutmoqda 📬",
    "Qani, biror belgi bering 📍",
    "Bugun ham jimlikni tanladingizmi? 😶",
    "Siz kelishingiz bilan chat jonlanadi ⚡",
    "Biror mavzu tashlab keting 💭",
    "Sizni kutib notification ham charchadi 🔔",
    "Qani, kim birinchi bo‘lib yozadi? 👀",
    "Bir kirib ko‘ring, balki yoqib qolar ⚡",
    "Chatga qaytish vaqti bo‘ldi 🕐",
    "Sizdan xabar kutish odat bo‘lib qoldi 📱",
    "Bir og‘iz gap bilan jimlikni tugating 🗣️",
    "Sizni kutib o‘tirganlar bor 🪑",
    "Qani, ko‘rinish bering, yo‘qolib ketmang 🫥",
    "Bugungi aktivlik sizdan boshlansin 🚀",
    "Bir xabar yozib qo‘ying, tamom 📩",
    "Chat sizni yana bir bor chaqiryapti 📢",
    "Qayerda bo‘lsangiz ham, bir salom tashlang 👋",
    "Sizni ko‘rmay ancha vaqt o‘tdi ⌛",
    "Bir daqiqalik tashrif ham yetadi ⏱️",
    "Siz kelmasangiz bu suhbat boshlanmaydi 🗨️",
    "Biror narsa yozing, o‘qib olamiz 👀",
    "Chatdagi sukutni siz buzishingiz mumkin 🔓",
    "Sizga joy tayyor 🪑",
    "Qani, bir ko‘rinib keting 📸",
    "Online bo‘lish vaqti keldi 📶",
    "Sizdan darak olish kerak bo‘lib qoldi 📣",
    "Biror emoji tashlab ketish ham mumkin 😶‍🌫️",
    "Chatga kirib, bir aylanish qilib chiqing 🔄",
    "Sizni kutish davom etmoqda ⏳",
    "Bir salom bilan hammasi boshlanadi 🌱",
    "Sizning xabaringiz bugungi topilma bo‘ladi 🔎",
    "Qani, chatni biroz jonlantiramiz ⚡",
    "Sizsiz bu yer juda sokin 🤫",
    "Bir xabar yozsangiz kifoya 📨",
    "Bugungi ko‘rinish hali bo‘lmadi 👀",
    "Sizni online ko‘rish kerak edi 📱",
    "Biror gap topib yozing 🤔",
    "Chatda siz uchun mikrofon tayyor 🎤",
    "Siz ham suhbatga qo‘shiling 🫱🏻‍🫲b",
    "Qani, jimlikka nuqta qo‘yamiz 🛑",
    "Bir kirib chiqing, keyin yana g‘oyib bo‘ling 🫥",
    "Sizni chaqirish yana takrorlanmoqda 🔁",
    "Chatning bir cheti sizni kutmoqda 📍",
    "Biror yangilik bormi? 📰",
    "Sizdan xabar kelishini kutyapmiz 📲",
    "Bugungi vazifa: chatga kirish ✅",
    "Qani, biror iz qoldiring 👣",
    "Sizning navbatingiz hali tugamadi 🎯",
    "Bir xabar tashlab, jimlikni buzib qo‘ying 🤫",
    "Chatga kirishga bahona topildi 📌",
    "Sizni kutish protokoli ishga tushdi ⚙️",
    "Biror narsa yozing, keyin bemalol keting 🚶",
    "Qani, ko‘rinmayapsiz-ku 🧐",
    "Sizni topish uchun qidiruv boshlandi 🔍",
    "Chatga bir kirib qo‘yish zarar qilmaydi 🙂",
    "Bir salom yuborishning vaqti keldi 👋",
    "Sizning xabaringiz hozir juda kerak 📨",
    "Qani, bugungi aktivlik qayerda? 📊",
    "Chat sizni kutib turibdi 🕰️",
    "Bir daqiqaga bo‘lsa ham qo‘shiling ✨",
    "Siz kelishingiz bilan gap boshlanadi 💬",
    "Biror mavzu ochib yuboring 💡",
    "Sizsiz chatning ovozi pastlab ketdi 🔉",
    "Qani, kimdir birinchi bo‘lib yozsin 😎",
    "Bir kirib, vaziyatni baholab chiqing 🧐",
    "Sizdan hali xabar yo‘q 📭",
    "Chatdagi bo‘sh joy sizni kutmoqda 🪑",
    "Bir ko‘rinish berib qo‘ying 📸",
    "Bugun ham sizdan xabar kutamiz 🌙",
    "Sizni chaqirish uchun yana bir signal 📡",
    "Bir dona salom bilan kifoyalanamiz 👋",
    "Chatga qaytish uchun hech qanday to‘siq yo‘q 🚪",
    "Qani, xabar tashlashni boshlaymiz 📨",
    "Sizdan biror gap kutilyapti 🗣️",
    "Biror narsa yozib, kayfiyatni o‘zgartiring 🌟",
    "Siz yo‘q paytda hammasi tinch 🤫",
    "Bir kirib chiqing, keyin yana ishlaringizga qayting 🫡",
    "Qani, bugungi xabaringizni kutamiz 📩",
    "Sizning ko‘rinishingiz hali qayd etilmadi 📝",
    "Chat sizdan biror belgi kutmoqda 🚨",
    "Biror gap yozing, jimlik yetarli 😶",
    "Sizni ko‘rish uchun yana bir sabab topildi 💡",
    "Bugungi tashrifingizni kutamiz 🎟️",
    "Bir kirib chiqing, qolganini keyin ko‘ramiz 👀",
    "Sizning navbatingiz keldi 🔔",
    "Chatda yana bir ovoz kerak 🎙️",
    "Bir xabar tashlang, bo‘ldi 📨",
    "Qani, biror yangilik bilan keling 📰",
    "Sizdan darak kelishini kutib turibmiz 📡",
    "Chatga kirish vaqti yaqinlashdi ⏰",
    "Bir ko‘rinib qo‘ying, yetarli 👁️",
    "Sizning xabaringiz uchun joy bor 📩",
    "Qani, bugun kim faol? 🫡",
    "Bir salom bilan boshlash mumkin 👋",
    "Sizni kutish davom etmoqda… ⏳",
    "Chatga qaytish belgisi berildi 🚦",
    "Biror narsa yozing, keyin o‘ylaymiz 🤔",
    "Sizsiz chat biroz g‘alati tuyulyapti ✨",
    "Qani, bir marta bo‘lsa ham ko‘rining 👀",
    "Sizga yana bir chaqiruv 📢",
    "Bir xabar tashlash vaqti keldi 📲",
    "Chatdagi jimlikni bugun siz buzishingiz mumkin 🔊",
    "Sizni kutib turibmiz, xolos 🪑",
    "Qani, biror belgi yuboring 📍",
    "Bugungi random xabar sizga atalgan 🎯",
    "Chatga kirib qo‘ying, qolganini vaziyat ko‘rsatadi 😌",
    "Biror gap yozib, o‘zingizni eslatib qo‘ying 📝",
    "Sizni ko‘rish vaqti bo‘ldi ⌚",
    "Qani, chatga bir qarab qo‘ying 👁️",
    "Bir salom tashlang, yetadi 👋",
    "Sizning navbatingiz hali kutilyapti 🎫",
    "Chat sizni yana chaqiryapti 📣",
    "Bir kirib chiqing, uzoq qolishingiz shart emas 🚪",
    "Bugun ham ko‘rinish berasiz degan umiddamiz 🌙",
    "Sizdan bir xabar — bizdan tinchlik 🤝",
    "Qani, suhbatni davom ettiramiz 💬",
    "Biror narsa yozing, qolganini o‘zi ketadi ⚡",
    "Sizni kutish rejimi hali ham yoqilgan 🔄",
    "Chatdagi bo‘sh joyingiz saqlanmoqda 🪑",
    "Bir marta ko‘rinib qo‘ying, keyin o‘zingiz bilasiz 😎",
    "Qani, xabar qani? 📩",
    "Sizdan hali ham darak yo‘q 🫤",
    "Bugungi tashrifingiz kutilmoqda 📅",
    "Biror emoji bo‘lsa ham tashlab keting 🙂",
    "Chat sizni kutib turibdi, oddiygina 👀",
    "Qani, biror gap bilan boshlaymiz 🗣️",
    "Sizni ko‘rish uchun yana bir chaqiruv 📢",
    "Bir kirib chiqing, keyin bemalol davom eting 🚶",
    "Chatga kirish uchun ayni vaqt ⏰",
    "Sizning xabaringiz hali kelmadi 📭",
    "Biror narsa yozing, jimlik zeriktirdi 🥱",
    "Qani, bugungi ko‘rinish bering 📸",
    "Sizsiz suhbat biroz bo‘sh 🧩",
    "Bir salom tashlab ketish mumkin 👋",
    "Sizni kutib turibmiz, shoshilmang 🫡",
    "Chat sizdan xabar kutmoqda 📬",
    "Biror gap bilan ko‘rinish bering 👀",
    "Qani, kimdir birinchi bo‘lib yozsin 🤫",
    "Sizning navbatingizni kutyapmiz 🎯",
    "Bir xabar yozing va g‘oyib bo‘ling 🫥",
    "Chatga qaytish uchun eshik ochiq 🚪",
    "Sizdan biror yangilik kutilyapti 💭",
    "Qani, bugungi aktivlikni ko‘rsatamiz 📈",
    "Bir ko‘rinib keting, bo‘ldi 😌",
    "Sizni kutish ham odat bo‘lib qoldi 🕰️",
    "Chatda sizning xabaringiz yetishmayapti 📱",
    "Bir kirib chiqing, suhbatni tekshirib keting 🔎",
    "Qani, biror narsa yozib qo‘ying 📝",
    "Sizning online bo‘lishingiz kutilmoqda 📶",
    "Chatga bir qarab qo‘ying, balki qiziq gap bordir 👀",
    "Bir dona xabar bilan kunni boshlab yuboring 🌅",
    "Sizni chaqirishning oxirgi signali emas bu 📢",
    "Qani, bir ko‘rinish bering 😎",
    "Chat sizni kutmoqda, xolos 📩",
    "Biror gap yozing, keyin yana g‘oyib bo‘ling 🫥",
    "Sizdan xabar kelishi kutilmoqda ⏳",
    "Bugun ham chatga tashrif buyuring 🌙",
    "Bir salom bilan boshlaymiz 👋",
    "Sizning joyingiz hali ham bo‘sh 🪑",
    "Qani, suhbatga qo‘shiling 🫱🏻‍🫲b",
    "Biror narsa yozing, qolganini ko‘ramiz 🔎",
    "Chatga kirish vaqti bo‘ldi 🔔",
    "Sizni kutib turibmiz, kechikmang ⌛",
    "Bir ko‘rinib qo‘ying, keyin ketavering 🚶",
    "Bugungi xabar sizdan bo‘lsin 📩",
    "Qani, chatni biroz jonlantiramiz ⚡",
    "Sizsiz bu yerda nimadir yetishmayapti 🧩",
    "Biror belgi yuboring, tirikligingizni bilaylik 🫡",
    "Chat sizni kutishdan zerikmayapti hali 😶",
    "Bir xabar tashlang, tamom 📲",
    "Qani, bugungi tashrifingizni kutamiz 📅",
    "Sizdan darak bo‘lmasa, yana chaqiramiz 📢",
    "Bir kirib chiqing, yo‘l ochiq 🚪",
    "Chatdagi jimlikka chek qo‘ying 🔊",
    "Sizning xabaringiz uchun joy tayyor 📩",
    "Qani, biror gap bilan chiqib keling 💬",
    "Bugun ham sizni kutib turibmiz 🌃",
    "Bir ko‘rinib, kunni yakunlab qo‘ying 🌙",
    "Sizdan xabar kelishini kutyapmiz 📱",
    "Chatga kirish — bugungi kichik vazifa ✅",
    "Qani, bir salom tashlab keting 👋",
    "Sizning navbatingiz yana keldi 🎯",
    "Biror narsa yozing, sukut yetarli 🤐",
    "Chat sizni yana bir bor eslatmoqda 🔔",
    "Bir kirib chiqing, keyin davom etamiz 🔄",
    "Qani, ko‘rinish bering, xolos 👀",
    "Sizdan hali ham xabar yo‘q 📭",
    "Bugungi aktivlik sizdan boshlansin 🚀",
    "Biror gap yozib, o‘zingizni eslatib qo‘ying 📝",
    "Chat sizni kutib turibdi, marhamat 🫡",
    "Bir salom tashlang va bemalol keting 👋",
    "Sizning xabaringiz bugungi topilma bo‘ladi 🔎",
    "Qani, suhbatga qaytamiz 💬",
    "Bir ko‘rinib qo‘ying, uzoq kutmaymiz ⏳",
    "Chatdagi bo‘shliqni to‘ldirib qo‘ying 🧩",
    "Sizni kutish rejimi hali o‘chirilmagan 🔄",
    "Bir xabar tashlang, keyin yana yo‘qoling 🫥",
    "Qani, kimdir javob bersin 📢",
    "Sizning online holatingiz kutilmoqda 📶",
    "Bugun chatda ko‘rinish kerak 📌",
    "Biror narsa yozing, kayfiyat o‘zgaradi ✨",
    "Sizsiz suhbat boshlanishi qiyin 🗣️",
    "Bir kirib chiqing, keyin yana o‘z ishingizga 😌",
    "Qani, bugungi salom qayerda? 👋",
    "Sizni chaqirish navbatdagi bosqichga o‘tdi 🚨",
    "Biror belgi qoldirib keting 👣",
    "Chat sizni kutib turibdi 📬",
    "Qani, bir ko‘rinib keting 👁️",
    "Bugungi tashrifingiz hali qayd etilmadi 📝",
    "Bir xabar yozing, jimlik tugasin 🔊",
    "Sizni kutib turibmiz, oddiygina 🪑",
    "Chatga qayting 🔄"
]

tag_status = {}

HELP_TEXT = (
    "╭━━━〔 ⚜️ 𝐁𝐮𝐲𝐫𝐮𝐪𝐥𝐚𝐫 𝐑𝐨'𝐲𝐱𝐚𝐭𝐢 ⚜️ 〕━━━╮\n"
    "┃  📜 𝐆𝐮𝐫𝐮𝐡𝐝𝐚 𝐢𝐬𝐡𝐥𝐚𝐲𝐝𝐢𝐠𝐚𝐧 𝐛𝐮𝐲𝐫𝐮𝐪𝐥𝐚𝐫\n"
    "╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    "  ▪ `.utag [matn]` — 𝐑𝐚𝐧𝐝𝐨𝐦 𝐬𝐨'𝐳𝐥𝐢 𝐭𝐚𝐠 𝐪𝐢𝐥𝐢𝐬𝐡;\n"
    "  ▪ `.atag [matn]` — 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 𝐭𝐚𝐠;\n"
    "  ▪ `.mention [matn]` — 𝐌𝐞𝐧𝐭𝐢𝐨𝐧 𝐭𝐚𝐠 𝐪𝐢𝐥𝐢𝐬𝐡;\n\n"
    "📊 𝐍𝐀𝐙𝐎𝐑𝐀𝐓\n"
    "  ▪ `.status` — Jarayon holati\n"
    "  ▪ `.count` — Guruh a'zolari statistikasi\n"
    "  ▪ `.stoped` / `.stop` — To'xtatish"
)


@app.on_message(filters.command("help", prefixes=".") & filters.me)
async def help_cmd(client, message):
    try:
        await message.delete()  # Buyruq xabarini o'chirish
    except Exception:
        pass
    await client.send_message(message.chat.id, HELP_TEXT)


@app.on_message(
    filters.command(["utag", "mention", "atag"], prefixes=".") & filters.me
)
async def tag_commands(client, message):
    command = message.command[0].lower()
    mode_map = {
        "utag": "yozuv",
        "mention": "mention",
        "atag": "username",
    }
    
    args = message.text.split(maxsplit=2)
    delay = 0.2
    custom_text = ""

    if len(args) > 1:
        try:
            delay = float(args[1])
            if len(args) > 2:
                custom_text = args[2]
        except ValueError:
            custom_text = " ".join(args[1:])

    # BUYRUQ XABARINI CHATDAN O'CHIRISH (.utag, .mention, .atag)
    try:
        await message.delete()
    except Exception:
        pass

    await run_user_tagger(client, message.chat.id, mode_map[command], custom_text, delay)


@app.on_message(filters.command("status", prefixes=".") & filters.me)
async def status_cmd(client, message):
    chat_id = message.chat.id
    
    try:
        await message.delete()  # Buyruq xabarini o'chirish
    except Exception:
        pass

    state = tag_status.get(chat_id)

    if not state:
        await client.send_message(chat_id, "ℹ️ Hozirda jarayon haqida ma'lumot yo‘q.")
        return

    total = state.get("total", 0)
    sent = state.get("sent", 0)
    failed = state.get("failed", 0)
    skipped = state.get("skipped", 0)
    active = state.get("active", False)

    remaining = max(total - sent - failed - skipped, 0)
    percent = round(sent / total * 100) if total else 0

    status_text = (
        "╔══〔 📊 𝐉𝐀𝐑𝐀𝐘𝐎𝐍 〕══╗\n\n"
        f"📌 Holat: {'🟢 Faol' if active else '⚪ To‘xtagan'}\n"
        f"👥 Jami: {total}\n"
        f"✅ Yuborilgan: {sent}\n"
        f"❌ Xatolar: {failed}\n"
        f"⏭ O‘tkazilgan: {skipped}\n"
        f"⌛ Qolgan: {remaining}\n"
        f"📈 Bajarildi: {percent}%\n\n"
        "╚════════════════════╝"
    )
    await client.send_message(chat_id, status_text)


@app.on_message(filters.command("count", prefixes=".") & filters.me)
async def count_cmd(client, message):
    chat_id = message.chat.id
    
    try:
        await message.delete()  # Buyruq xabarini o'chirish
    except Exception:
        pass

    status_msg = await client.send_message(chat_id, "🔎 Guruh a'zolari hisoblanmoqda...")

    total = 0
    eligible = 0
    bots = 0
    deleted = 0
    no_username = 0
    errors = 0

    try:
        async for member in client.get_chat_members(chat_id):
            total += 1
            user = member.user

            if user.is_bot:
                bots += 1
                continue

            if getattr(user, "is_deleted", False):
                deleted += 1
                continue

            if not user.first_name:
                errors += 1
                continue

            eligible += 1

            if not user.username:
                no_username += 1

    except Exception as e:
        await status_msg.edit_text(f"❌ Hisoblashda xatolik:\n{e}")
        return

    await status_msg.edit_text(
        "╔══〔 👥 𝐆𝐔𝐑𝐔𝐇 𝐒𝐓𝐀𝐓𝐈𝐒𝐓𝐈𝐊𝐀𝐒𝐈 〕══╗\n\n"
        f"👥 Jami a'zolar: {total}\n"
        f"✅ Tag uchun mos: {eligible}\n"
        f"🤖 Botlar: {bots}\n"
        f"🗑 O‘chirilgan akkauntlar: {deleted}\n"
        f"🔹 Username yo‘q: {no_username}\n"
        f"⚠️ Ismi yo‘q: {errors}\n\n"
        "╚══════════════════════════╝"
    )


@app.on_message(filters.command(["stop", "stoped"], prefixes=".") & filters.me)
async def stop_utag(client, message):
    chat_id = message.chat.id
    
    try:
        await message.delete()  # Buyruq xabarini o'chirish (.stop / .stoped)
    except Exception:
        pass

    state = tag_status.get(chat_id)

    if state and state.get("active"):
        state["active"] = False
        await client.send_message(chat_id, "🛑 𝗔𝘇𝗼𝗯𝗹𝗮𝘀𝗵 𝘅𝗶𝘇𝗺𝗮𝘁𝗶 𝘁𝗼'𝘅𝘁𝗮𝘁𝗶𝗹𝗱𝗶.")
    else:
        await client.send_message(chat_id, "ℹ️ Hozirda faol xizmat mavjud emas.")


async def update_panel_async(status_msg, tag_title, sent_count, total_members, delay, start_time):
    """Jonli statistika panelini tahrirlab yangilash"""
    try:
        elapsed_time = time.time() - start_time
        speed = round(sent_count / elapsed_time, 1) if elapsed_time > 0 else 0
        remaining_sec = int((total_members - sent_count) * delay)

        panel_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📣 {tag_title} [👥 BARCHA]\n"
            f"📊 Yuborildi: {sent_count}/{total_members}\n"
            f"⏱ Delay: {delay}s\n"
            f"⚡ Tezlik: {speed}/s | ⏳ Qolgan: {remaining_sec}s\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛑 To'xtatish: .stoped"
        )
        await status_msg.edit_text(panel_text)
    except Exception:
        pass


async def run_user_tagger(client, chat_id, mode, custom_text="", delay=0.2):
    current = tag_status.get(chat_id)
    if current and current.get("active"):
        await client.send_message(
            chat_id,
            "⚠️ Bu guruhda jarayon allaqachon ishlayapti.\n"
            "Holat: `.status`\n"
            "To‘xtatish: `.stop`"
        )
        return

    # 1. BOSHILANGANI HAQIDA ALOHIDA YANGI XABAR YUBORILADI
    await client.send_message(chat_id, "😈🚀𝗔𝘇𝗼𝗯𝗹𝗮𝘀𝗵 𝘅𝗶𝘇𝗺𝗮𝘁𝗶 𝗯𝗼𝘀𝗵𝗹𝗮𝗻𝗱𝗶..")

    members = []

    try:
        async for member in client.get_chat_members(chat_id):
            user = member.user

            if user.is_bot or getattr(user, "is_deleted", False) or not user.first_name:
                continue

            if mode == "username" and not user.username:
                continue

            members.append(user)

    except Exception as e:
        await client.send_message(chat_id, f"❌ Xatolik: {e}")
        return

    if not members:
        await client.send_message(chat_id, "ℹ️ Belgilash uchun mos foydalanuvchi topilmadi.")
        return

    total_members = len(members)
    state = {
        "active": True,
        "total": total_members,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
    }
    tag_status[chat_id] = state

    start_time = time.time()

    mode_titles = {
        "yozuv": "Random Utag",
        "mention": "Mention",
        "username": "Username Utag"
    }
    tag_title = mode_titles.get(mode, "Tag")

    # 2. STATISTIKA JONLI PANELI UCHUN ALOHIDA XABAR YUBORILADI
    status_msg = await client.send_message(
        chat_id,
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📣 {tag_title} [👥 BARCHA]\n"
        f"📊 Yuborildi: 0/{total_members}\n"
        f"⏱ Delay: {delay}s\n"
        f"⚡ Tezlik: 0/s | ⏳ Qolgan: {int(total_members * delay)}s\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛑 To'xtatish: .stoped"
    )

    is_completed = True
    sent_count = 0

    for user in members:
        if not state["active"]:
            is_completed = False
            break

        sent_count += 1
        name = user.first_name

        if mode == "yozuv":
            word = random.choice(RANDOM_SOZLAR)
            tag_part = f"[{name}](tg://user?id={user.id}) {word}"
        elif mode == "mention":
            tag_part = f"[{name}](tg://user?id={user.id})"
        elif mode == "username":
            tag_part = f"@{user.username}"

        text_to_send = f"{custom_text} {tag_part}" if custom_text else tag_part

        try:
            await client.send_message(chat_id, text_to_send, disable_web_page_preview=True)
            state["sent"] += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)
            if not state["active"]:
                is_completed = False
                break
            try:
                await client.send_message(chat_id, text_to_send, disable_web_page_preview=True)
                state["sent"] += 1
            except Exception:
                state["failed"] += 1

        except Exception:
            state["failed"] += 1

        # Panelni har 5 ta xabarda asinxron yangilash
        if sent_count % 5 == 0 or sent_count == total_members:
            asyncio.create_task(update_panel_async(status_msg, tag_title, sent_count, total_members, delay, start_time))

        await asyncio.sleep(delay)

    # 3. YAKUNLANGANI HAQIDA ALOHIDA YANGI XABAR YUBORILADI
    if is_completed and state.get("active"):
        await client.send_message(chat_id, "😈🚀𝗔𝘇𝗼𝗯𝗹𝗮𝘀𝗵 𝘅𝗶𝘇𝗺𝗮𝘁𝗶 𝘆𝗮𝗸𝘂𝗻𝗹𝗮𝗻𝗱𝗶")

    state["active"] = False


if __name__ == "__main__":
    print("⚜️ Utag Userbot ishga tushmoqda...")
    app.run()

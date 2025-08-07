"""
WhatsApp-бот для дрон-контроля (эмуляция).
"""
def start_whatsapp_bot():
    print("WhatsApp-бот запущен")
    while True:
        msg = input("User: ")
        if msg == "status":
            print("System: All drones are OK.")
        else:
            print("System: Unknown command.")

let currentLang = "en";

function sendCommand(cmd) {
    const status = document.getElementById("status");
    status.textContent = `Отправлена команда: ${cmd}`;
    // Имитация отправки команды в backend
    console.log(`Команда "${cmd}" отправлена дрону (${currentLang})`);
}

function changeLanguage() {
    const select = document.getElementById("languageSelect");
    currentLang = select.value;
    console.log("Язык интерфейса изменён на", currentLang);
    // Здесь можно подгружать языковые строки из API или файла
}

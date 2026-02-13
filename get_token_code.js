// Discord Token Alma Kodu
// Bu kodu kopyalayın, Discord'un açık olduğu tarayıcı sekmesinde F12'ye basın.
// "Console" sekmesine gelin, bu kodu yapıştırın ve Enter'a basın.

(function() {
    let token = '';
    try {
        // Webpack modülleri üzerinden tokeni bulmayı dener
        token = (window.webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken).exports.default.getToken();
    } catch (e) {
        try {
             token = (window.webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.getToken).exports.getToken();
        } catch (e2) {
            console.error("Token otomatik olarak alınamadı.");
        }
    }

    if (token) {
        console.clear();
        console.log('%cDİKKAT! BU TOKENİ KİMSEYLE PAYLAŞMAYIN!', 'color: red; font-size: 30px; font-weight: bold; text-shadow: 2px 2px black;');
        console.log('%cTokeniniz aşağıdadır:', 'color: white; font-size: 20px;');
        console.log('%c' + token, 'color: #00ff00; font-size: 18px; background: #000; padding: 10px; border-radius: 10px; border: 2px solid #00ff00;');
        
        // Tokeni otomatik olarak panoya kopyalamayı dene
        try {
            copy(token); 
            console.log('%cToken otomatik olarak panoya kopyalandı!', 'color: yellow; font-size: 16px; font-style: italic;');
        } catch (e) {
            console.log('Otomatik kopyalama başarısız, lütfen yukarıdaki tokeni manuel olarak seçip kopyalayın.');
        }
    } else {
        console.log('%cToken bulunamadı! Lütfen hesabınıza giriş yaptığınızdan emin olun.', 'color: red; font-weight: bold;');
    }
})();

/* kampalanlar.com — harita sayfası. Leaflet yüklendikten sonra çalışır. */
(function () {
  "use strict";
  var kutu = document.getElementById("buyuk-harita");
  if (!kutu) return;

  function baslat() {
    if (typeof L === "undefined") { setTimeout(baslat, 60); return; }

    var harita = L.map(kutu, { scrollWheelZoom: false }).setView([39.2, 35.0], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(harita);

    var katman = L.layerGroup().addTo(harita);
    var kayitlar = [];

    var kampIkon = L.divIcon({ className: "ig ig-kamp", html: "⛺", iconSize: [26, 26] });
    var digerIkon = L.divIcon({ className: "ig ig-diger", html: "•", iconSize: [20, 20] });

    function metin(a) {
      var s = "<b>" + a.ad + "</b><br>" + a.tur_bilgi_ad + " · " + a.il;
      if (a.hektar_yazi) s += "<br>" + a.hektar_yazi + " ha";
      s += a.kamp_izni_resmi
        ? '<br><span style="color:#1b5e3f"><b>⛺ Resmî kayıtta kamp geçiyor</b></span>'
        : '<br><span style="color:#8a6d3b">Resmî kayıtta kamp belirtilmiyor</span>';
      return s + '<br><a href="' + a.url + '">Ayrıntı →</a>';
    }

    function ciz() {
      var yalnizKamp = document.getElementById("sadece-kamp").checked;
      var tur = document.getElementById("tur-filtre").value;
      katman.clearLayers();
      var n = 0;
      kayitlar.forEach(function (a) {
        if (yalnizKamp && !a.kamp_izni_resmi) return;
        if (tur && a.tur !== tur) return;
        L.marker([a.lat, a.lng], { icon: a.kamp_izni_resmi ? kampIkon : digerIkon })
          .bindPopup(metin(a)).addTo(katman);
        n++;
      });
      kutu.setAttribute("aria-label", n + " korunan alan haritada gösteriliyor");
    }

    fetch("/veri/korunan-alanlar.json")
      .then(function (y) { return y.json(); })
      .then(function (veri) {
        kayitlar = veri.filter(function (a) {
          return a.lat !== null && a.koordinat_durum !== "supheli";
        }).map(function (a) {
          a.tur_bilgi_ad = { milli_park: "Milli Park", tabiat_parki: "Tabiat Parkı",
                             tabiati_koruma: "Tabiatı Koruma Alanı" }[a.tur] || "";
          return a;
        });
        ciz();
      })
      .catch(function () {
        kutu.innerHTML = '<p class="bos">Harita verisi yüklenemedi. ' +
          '<a href="/il/">İllere göre listeye</a> geçebilirsiniz.</p>';
      });

    ["sadece-kamp", "tur-filtre"].forEach(function (kimlik) {
      var e = document.getElementById(kimlik);
      if (e) e.addEventListener("change", ciz);
    });

    var konum = document.getElementById("konum");
    if (konum && navigator.geolocation) {
      konum.addEventListener("click", function () {
        konum.textContent = "Konum alınıyor…";
        navigator.geolocation.getCurrentPosition(function (p) {
          harita.setView([p.coords.latitude, p.coords.longitude], 9);
          L.circleMarker([p.coords.latitude, p.coords.longitude],
            { radius: 8, color: "#1b5e3f", fillOpacity: 0.6 }).addTo(harita);
          konum.textContent = "📍 Bana yakın";
        }, function () {
          konum.textContent = "Konum alınamadı";
          setTimeout(function () { konum.textContent = "📍 Bana yakın"; }, 2000);
        });
      });
    } else if (konum) {
      konum.hidden = true;
    }
  }

  baslat();
})();

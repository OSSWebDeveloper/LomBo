/* Pul maydonlari: yozayotganda har 3 raqamdan keyin bo'shliq qo'yiladi.
   «7000000» -> «7 000 000». Serverga baribir toza son boradi — `PulField`
   bo'shliqlarni o'zi tashlaydi (`formatlash.pul_son`).

   Bu fayl `base.html` da ulanadi, ya'ni `class="pul"` maydoni bo'lgan HAR
   QANDAY sahifada ishlaydi (shartnoma formasi, grafik kalkulyatori). Ilgari
   kod faqat `contract_form.html` ichida turgan edi — grafik bo'limi
   qo'shilganda o'sha sahifada formatlash ishlamay qolgan edi.

   Boshqa skriptlar uchun `window.pul` ochiq: `pul.son()`, `pul.format()`. */
(function(){
  function raqam(matn){
    return String(matn == null ? '' : matn).replace(/[^\d]/g, '').replace(/^0+(?=\d)/, '');
  }
  function format(matn){
    return raqam(matn).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }
  function son(matn){
    var r = raqam(matn);
    return r ? parseInt(r, 10) : 0;
  }
  function maydon(inp){
    var eski = inp.value;
    var yangi = format(eski);
    if (yangi === eski) return;
    // Kursordan oldingi raqamlar sonini eslab qolamiz — qayta yozgach o'sha joyga qaytaramiz
    var kursor = inp.selectionStart;
    var oldingiRaqam = kursor === null ? -1 : (eski.slice(0, kursor).match(/\d/g) || []).length;
    inp.value = yangi;
    if (oldingiRaqam < 0) return;
    var joy = 0, sanoq = 0;
    while (joy < yangi.length && sanoq < oldingiRaqam){
      if (yangi.charCodeAt(joy) >= 48 && yangi.charCodeAt(joy) <= 57) sanoq++;
      joy++;
    }
    try { inp.setSelectionRange(joy, joy); } catch (e){}
  }

  document.addEventListener('input', function(e){
    if (e.target.classList && e.target.classList.contains('pul')) maydon(e.target);
  });
  document.querySelectorAll('.pul').forEach(maydon);

  window.pul = {raqam: raqam, format: format, son: son, maydon: maydon};
})();

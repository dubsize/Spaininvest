/* Mémoria — scripts v2 (chargé en defer sur toutes les pages). */
(function () {
  // [WHATSAPP] : numéro au format international, chiffres uniquement (ex. 34600123456).
  // Tant qu'il n'est pas renseigné, le bouton renvoie vers le formulaire de contact.
  var WHATSAPP = '[WHATSAPP]';

  var lang = (document.documentElement.lang || 'fr').slice(0, 2);
  var L = {
    fr: { label: 'Écrivez-nous sur WhatsApp', text: 'Bonjour Mémoria, ', home: '/' },
    en: { label: 'Message us on WhatsApp', text: 'Hello Mémoria, ', home: '/en/' },
    he: { label: 'כתבו לנו בוואטסאפ', text: 'שלום Mémoria, ', home: '/he/' }
  }[lang] || null;
  if (!L || document.body.classList.contains('cap-body')) return;

  var ok = /^\d{8,15}$/.test(WHATSAPP);
  var a = document.createElement('a');
  a.className = 'wa-float';
  a.href = ok ? 'https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(L.text) : L.home + '#contact';
  if (ok) { a.target = '_blank'; a.rel = 'noopener'; }
  a.setAttribute('aria-label', L.label);
  a.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg><span>' + L.label + '</span>';
  document.body.appendChild(a);
})();

(function(){
  var KEY='memoria_cookie_consent';
  var banner=document.getElementById('cookie-banner');
  if(!banner) return;

  function get(){
    try{ return localStorage.getItem(KEY); }catch(e){ return null; }
  }
  function set(v){
    try{ localStorage.setItem(KEY,v); }catch(e){}
  }

  if(!get()){
    // léger délai pour ne pas gêner le premier rendu
    setTimeout(function(){ banner.classList.add('show'); },700);
  }

  var accept=document.getElementById('cb-accept');
  var reject=document.getElementById('cb-reject');

  if(accept) accept.addEventListener('click',function(){
    set('all');
    banner.classList.remove('show');
    // Si un outil d'analyse est ajouté un jour, l'initialiser ICI uniquement.
  });

  if(reject) reject.addEventListener('click',function(){
    set('essential');
    banner.classList.remove('show');
  });
})();

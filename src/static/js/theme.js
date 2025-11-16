// Theme toggle: stores choice in cookie and applies .dark-theme on body
(function(){
  const toggle = document.getElementById('theme-toggle');
  if(!toggle) return;
  function setCookie(name,value,days){
    let expires="";
    if(days){
      const d=new Date(); d.setTime(d.getTime()+days*24*60*60*1000); expires='; expires='+d.toUTCString();
    }
    document.cookie = name+'='+value+expires+'; path=/';
  }
  function getCookie(name){
    const v = document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');
    return v? v[2] : null;
  }
  function applyTheme(theme){
    if(theme==='dark') document.body.classList.add('dark-theme');
    else document.body.classList.remove('dark-theme');
    toggle.textContent = theme==='dark' ? '☀️' : '🌙';
  }
  // initialize
  const saved = getCookie('site_theme') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(saved);
  toggle.addEventListener('click', ()=>{
    const isDark = document.body.classList.toggle('dark-theme');
    const theme = isDark ? 'dark' : 'light';
    setCookie('site_theme', theme, 365);
    toggle.textContent = isDark ? '☀️' : '🌙';
  });
})();

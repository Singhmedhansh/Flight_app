(function(){
  const avatarToggle = document.getElementById('user-menu-btn');
  const dropdown = document.getElementById('user-dropdown');
  const changePhotoBtn = document.getElementById('change-photo');
  const headerInput = document.getElementById('header_profile_photo');
  const modal = document.getElementById('profile-modal');
  const closeBtn = document.getElementById('modal-close');
  const cancelBtn = document.getElementById('modal-cancel');
  const input = document.getElementById('profile_photo');
  const preview = document.getElementById('preview-container');
  const previewImg = document.getElementById('preview-img');
  const themeToggle = document.getElementById('theme-toggle');
  const dropdownTheme = document.getElementById('dropdown-theme-toggle');

  function closeDropdown(){
    if(dropdown){ dropdown.classList.remove('open'); dropdown.setAttribute('aria-hidden','true'); }
    if(avatarToggle){ avatarToggle.setAttribute('aria-expanded','false'); avatarToggle.classList.remove('open'); }
  }

  function openDropdown(){
    if(dropdown){ dropdown.classList.add('open'); dropdown.setAttribute('aria-hidden','false'); }
    if(avatarToggle){ avatarToggle.setAttribute('aria-expanded','true'); avatarToggle.classList.add('open'); }
  }

  if(avatarToggle){
    avatarToggle.addEventListener('click', (e)=>{
      e.stopPropagation();
      if(dropdown && dropdown.classList.contains('open')) closeDropdown(); else openDropdown();
    });
  }

  // Close dropdown when clicking outside
  document.addEventListener('click', (e)=>{
    if(!e.target.closest('.avatar-wrap')) closeDropdown();
  });

  if(changePhotoBtn){
    changePhotoBtn.addEventListener('click', (e)=>{
      e.stopPropagation();
      // If a header hidden file input exists, use it for quick selection/upload
      if(headerInput){
        headerInput.click();
        closeDropdown();
        return;
      }
      if(modal){ modal.style.display='flex'; modal.setAttribute('aria-hidden','false'); }
      closeDropdown();
    });
  }

  if(closeBtn){
    closeBtn.addEventListener('click', ()=>{
      if(modal){ modal.style.display='none'; modal.setAttribute('aria-hidden','true'); }
    });
  }
  if(cancelBtn){
    cancelBtn.addEventListener('click', ()=>{
      if(modal){ modal.style.display='none'; modal.setAttribute('aria-hidden','true'); }
    });
  }

  if(input){
    input.addEventListener('change', (e)=>{
      const f = e.target.files[0];
      if(!f) return;
      const url = URL.createObjectURL(f);
      previewImg.src = url;
      preview.style.display = 'block';
    });
  }

  // Header quick-upload handler: upload via fetch and refresh avatar on success
  if(headerInput){
    headerInput.addEventListener('change', async (e)=>{
      const f = e.target.files[0];
      if(!f) return;
      const fd = new FormData();
      fd.append('profile_photo', f);
      try{
        const res = await fetch('/upload_profile_photo', { method: 'POST', body: fd });
        // Update avatar if upload succeeded. Flask redirects on success; treat any ok response as success.
        if(res.ok){
          // Update profile image src with cache-busting query so browser fetches new file
          const img = document.getElementById('profile-img');
          if(img){
            const src = img.getAttribute('src') || '';
            // If using default svg, try to construct uploads path; otherwise just bust cache
            const newSrc = src.includes('/static/uploads/') ? src.split('?')[0] + '?t=' + Date.now() : src + '?t=' + Date.now();
            img.setAttribute('src', newSrc);
            // animate
            img.classList.remove('updated');
            // Force reflow to restart animation
            void img.offsetWidth;
            img.classList.add('updated');
          } else {
            window.location.reload();
          }
        } else {
          window.location.reload();
        }
      } catch(err){
        console.error('Upload failed', err);
        alert('Upload failed');
      }
    });
  }

  // wire theme toggles to same action
  function triggerThemeToggle(){
    const ev = new Event('click');
    // Reuse theme.js toggle button if present
    const btn = document.getElementById('theme-toggle');
    if(btn){ btn.dispatchEvent(ev); }
  }
  if(themeToggle){ themeToggle.addEventListener('click', triggerThemeToggle); }
  if(dropdownTheme){ dropdownTheme.addEventListener('click', ()=>{ triggerThemeToggle(); closeDropdown(); }); }

})();

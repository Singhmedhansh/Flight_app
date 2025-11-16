// Smooth scroll + autofocus for the Explore button
document.addEventListener('DOMContentLoaded', function () {
  const exploreLinks = document.querySelectorAll('a[href="#search-section"]');
  const searchSection = document.getElementById('search-section');
  const originInput = document.getElementById('origin');

  function goToSearch(e) {
    // allow normal middle-click / new-tab
    if (e) e.preventDefault();
    if (!searchSection) return;
    // Use smooth scrolling and then focus the origin input
    searchSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Add a visual highlight to the search container to guide the user
    const highlightTarget = searchSection.closest('.card') || searchSection;
    if (highlightTarget) {
      highlightTarget.classList.add('search-highlight');
      // remove highlight after animation completes
      setTimeout(function () { highlightTarget.classList.remove('search-highlight'); }, 1400);
    }
    // Focus after a short delay so browsers that animate scrolling won't steal focus
    setTimeout(function () {
      if (originInput) {
        originInput.focus({ preventScroll: true });
        // select text if any for quick replacement
        originInput.select();
      }
    }, 420);
  }

  exploreLinks.forEach(function (a) {
    a.addEventListener('click', goToSearch);
  });

  // Optional: if user lands on the page with the hash already present, focus immediately
  if (window.location.hash === '#search-section') {
    setTimeout(function () {
      if (originInput) originInput.focus({ preventScroll: true });
    }, 300);
  }
});

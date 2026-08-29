// Mr Spelling — one authored motion grammar: elements "beat in" as they
// enter the viewport (ties motion to the site's own rhythm/song mechanism
// instead of a generic fade-up). Progressive enhancement only: everything
// is fully visible without JS (see .no-js rule in site.css) and this does
// nothing when prefers-reduced-motion is set.
(function () {
  document.documentElement.classList.remove('no-js');

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;

  var targets = document.querySelectorAll('.beat, .beat-group');
  if (!targets.length) return;

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      var group = el.classList.contains('beat-group') ? el : null;
      if (group) {
        var children = group.querySelectorAll('.beat-child');
        children.forEach(function (child, i) {
          child.style.transitionDelay = (i * 55) + 'ms';
        });
      }
      el.classList.add('is-in');
      io.unobserve(el);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

  targets.forEach(function (el) { io.observe(el); });
})();

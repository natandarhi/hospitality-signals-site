// Scroll effects. CSS scroll-driven animations do the heavy lifting where the
// browser supports them; this file adds the floating bar and a fallback reveal.
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Floating bar on the home page, once the big masthead has scrolled away.
  var bar = document.querySelector('.minibar-float');
  var mast = document.querySelector('.masthead-large');
  if (bar && mast && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (e) {
      bar.classList.toggle('is-on', !e[0].isIntersecting);
    }).observe(mast);
  }

  // Reading progress on articles.
  var progress = document.querySelector('.progress');
  if (progress) {
    var tick = function () {
      var max = root.scrollHeight - innerHeight;
      progress.style.transform = 'scaleX(' + (max > 0 ? scrollY / max : 0) + ')';
    };
    addEventListener('scroll', tick, { passive: true });
    tick();
  }

  // Fallback for browsers without scroll-driven animations: reveal and parallax by script.
  if (reduce || (window.CSS && CSS.supports('animation-timeline: view()'))) return;
  root.classList.add('js-motion');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.reveal').forEach(function (el) {
      if (el.getBoundingClientRect().top < innerHeight) el.classList.add('is-in'); else io.observe(el);
    });
  }
  var layers = [].slice.call(document.querySelectorAll('.hero-photo .photo-frame > *, .cover-photo .photo-frame > *, .chapter-photo .photo-frame > *'));
  var frame = false;
  var drift = function () {
    frame = false;
    layers.forEach(function (el) {
      var r = el.parentNode.getBoundingClientRect();
      var t = (r.top + r.height / 2 - innerHeight / 2) / innerHeight; // -1..1 around centre
      el.style.transform = 'scale(1.15) translate3d(0,' + (t * -7).toFixed(2) + '%,0)';
    });
  };
  addEventListener('scroll', function () { if (!frame) { frame = true; requestAnimationFrame(drift); } }, { passive: true });
  drift();
})();


// Edition home: scroll-linked opening, inked statement, horizontal reel, lit index.
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var opening = document.querySelector('[data-opening]');
  var sitebar = document.querySelector('[data-sitebar]');
  var statement = document.querySelector('[data-statement]');
  var reel = document.querySelector('[data-reel]');
  var rows = [].slice.call(document.querySelectorAll('.index-row'));
  var covers = [].slice.call(document.querySelectorAll('.cover-photo .photo-frame, .cover-visual picture'));
  if (!opening && !covers.length) return;

  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var range = function (p, a, b) { return clamp((p - a) / (b - a), 0, 1); };

  var stage = opening && opening.querySelector('.opening-stage');
  var mark = opening && opening.querySelector('.opening-mark');
  var win = opening && opening.querySelector('.window');
  var dot = mark && mark.querySelector('.logo-dot');
  var words = statement ? [].slice.call(statement.querySelectorAll('.w')) : [];
  var track = reel && reel.querySelector('.reel-track');
  var mobile = window.matchMedia('(max-width: 760px)');
  var dotX = 0, dotY = 0, maxR = 0;

  function measure() {
    if (dot && stage) {
      var prev = mark.style.transform; mark.style.transform = 'none';
      var d = dot.getBoundingClientRect(), s = stage.getBoundingClientRect();
      mark.style.transform = prev;
      dotX = d.left + d.width / 2 - s.left; dotY = d.top + d.height / 2 - s.top;
      maxR = Math.hypot(Math.max(dotX, s.width - dotX), Math.max(dotY, s.height - dotY));
      win.style.setProperty('--cx', dotX + 'px'); win.style.setProperty('--cy', dotY + 'px');
      win.dataset.r0 = d.width / 2;
    }
    if (reel && track) {
      reel.style.height = mobile.matches || reduce ? '' : (track.scrollWidth - innerWidth + innerHeight) + 'px';
    }
  }

  function frame() {
    ticking = false;
    var vh = innerHeight;
    if (opening && !reduce) {
      var r = opening.getBoundingClientRect();
      var p = clamp(-r.top / (r.height - vh), 0, 1);
      var a = ease(range(p, 0, .55));
      if (win) {
        var r0 = +win.dataset.r0 || 6;
        win.style.setProperty('--r', (r0 + (maxR - r0) * a).toFixed(1) + 'px');
        win.style.setProperty('--t', ease(range(p, .5, .8)).toFixed(3));
        win.style.setProperty('--d', (1 - range(a, .04, .3)).toFixed(3));
      }
      if (mark) {
        mark.style.opacity = (1 - range(p, .2, .5)).toFixed(3);
        mark.style.transform = 'scale(' + (1 + range(p, 0, .5) * .18).toFixed(3) + ')';
      }
      if (sitebar) sitebar.classList.toggle('is-on', p > .92 || r.bottom < vh);
    } else if (sitebar) {
      sitebar.classList.add('is-on');
    }
    if (words.length) {
      var sr = statement.getBoundingClientRect();
      var sp = reduce ? 1 : range(vh * .85 - sr.top, 0, sr.height * .9 + vh * .15);
      var n = Math.round(sp * words.length);
      for (var i = 0; i < words.length; i++) words[i].classList.toggle('on', i < n);
    }
    if (track && !mobile.matches && !reduce) {
      var rr = reel.getBoundingClientRect();
      var rp = clamp(-rr.top / (rr.height - vh), 0, 1);
      track.style.transform = 'translate3d(' + (-(track.scrollWidth - innerWidth) * rp).toFixed(1) + 'px,0,0)';
    }
    if (rows.length) {
      var mid = vh * .5, best = null, bd = 1e9;
      rows.forEach(function (row) {
        var b = row.getBoundingClientRect(), dd = Math.abs(b.top + b.height / 2 - mid);
        if (dd < bd) { bd = dd; best = row; }
      });
      rows.forEach(function (row) { row.classList.toggle('is-on', row === best && bd < vh * .3); });
    }
    covers.forEach(function (c) {
      if (reduce) return;
      var b = c.getBoundingClientRect();
      var cp = range(vh - b.top, 0, vh * .8);
      c.style.setProperty('--ci', ((1 - ease(cp)) * 8).toFixed(2) + '%');
    });
  }

  var ticking = false;
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', function () { measure(); frame(); });
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(function () { measure(); frame(); });
  measure(); frame();
})();

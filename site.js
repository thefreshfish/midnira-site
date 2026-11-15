(function () {
  var root = document.documentElement;
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function clock(d) {
    var h = d.getHours(), m = d.getMinutes();
    return ((h % 12) || 12) + ':' + (m < 10 ? '0' : '') + m + ' ' + (h < 12 ? 'AM' : 'PM');
  }

  /* Sky. A small seeded generator keeps the stars the same on every visit. */
  function generator(seed) {
    return function () {
      seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  var css = getComputedStyle(root);
  var moon = css.getPropertyValue('--moon').trim();
  var tints = [moon, moon, moon, moon, css.getPropertyValue('--agent').trim(), css.getPropertyValue('--lamp').trim()];
  var skies = document.querySelectorAll('canvas.stars');

  function paint(canvas) {
    if (!canvas.getContext) return;
    var box = canvas.parentNode, ctx = canvas.getContext('2d');
    var w = box.clientWidth, h = box.clientHeight;
    var reach = (parseFloat(canvas.getAttribute('data-reach')) || 1) * h;   // how far down the stars go
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var rand = generator(parseInt(canvas.getAttribute('data-seed'), 10) || 1);
    var count = Math.min(460, Math.round(w * reach / 3000));
    for (var i = 0; i < count; i++) {
      var x = rand() * w;
      var y = Math.pow(rand(), 1.5) * reach;
      var r = 0.35 + Math.pow(rand(), 3) * 1.15;
      ctx.globalAlpha = (0.22 + rand() * 0.6) * (1 - 0.85 * y / reach);
      ctx.fillStyle = tints[Math.floor(rand() * tints.length)];
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
  function paintAll() { for (var i = 0; i < skies.length; i++) paint(skies[i]); }
  paintAll();
  var resizing;
  window.addEventListener('resize', function () { clearTimeout(resizing); resizing = setTimeout(paintAll, 150); });

  var hero = document.querySelector('.hero');
  if (hero) {
    var spark = generator(905);
    for (var s = 0; s < 6; s++) {
      var star = document.createElement('span');
      star.className = 'twinkle';
      star.style.left = (spark() * 100).toFixed(2) + '%';
      star.style.top = (spark() * 40).toFixed(2) + '%';
      star.style.setProperty('--d', (4 + spark() * 4).toFixed(1) + 's');
      star.style.setProperty('--o', (-spark() * 8).toFixed(1) + 's');
      hero.appendChild(star);
    }
  }

  /* The dial: show the visitor's own time, and pair each mark with its entry. */
  var dial = document.querySelector('.dial');
  if (dial) {
    var hand = dial.querySelector('.now');
    var timeText = dial.querySelector('.dial-time');
    var stateText = dial.querySelector('.dial-state');
    var tick = function () {
      var d = new Date(), hours = d.getHours() + d.getMinutes() / 60;
      var open = hours >= 8 && hours < 18;
      hand.setAttribute('transform', 'rotate(' + (hours / 24 * 360).toFixed(2) + ' 300 300)');
      hand.removeAttribute('display');
      timeText.textContent = clock(d);
      stateText.textContent = open ? 'Office hours' : 'After hours';
      stateText.setAttribute('class', 'dial-state ' + (open ? 'is-day' : 'is-night'));
    };
    tick();
    setInterval(tick, 20000);

    /* A small bead runs round the inner ring once a minute, in step with the real second. */
    var bead = dial.querySelector('.seconds');
    if (bead) {
      var started = new Date();
      bead.style.animationDelay = '-' + (started.getSeconds() + started.getMilliseconds() / 1000).toFixed(2) + 's';
    }

    /* The lower small dial shows the moon's real phase, from the mean
       length of a lunar month counted from a known new moon. */
    var lit = dial.querySelector('.moon-lit');
    var moonName = document.getElementById('moon-name');
    if (lit) {
      var month = 29.530588853;
      var age = ((Date.now() - Date.UTC(2000, 0, 6, 18, 14)) / 86400000) % month;
      if (age < 0) age += month;
      var phase = age / month, bulge = Math.cos(phase * 2 * Math.PI), waxing = phase < 0.5, R = 19;
      var limb = waxing ? 1 : 0, edge = (bulge > 0) === waxing ? 0 : 1;
      lit.setAttribute('d', 'M 0 ' + (-R) + ' A ' + R + ' ' + R + ' 0 0 ' + limb + ' 0 ' + R +
        ' A ' + (R * Math.abs(bulge)).toFixed(2) + ' ' + R + ' 0 0 ' + edge + ' 0 ' + (-R) + ' Z');
      var names = [[0.03, 'New moon'], [0.22, 'Waxing crescent moon'], [0.28, 'First quarter moon'], [0.47, 'Waxing gibbous moon'],
        [0.53, 'Full moon'], [0.72, 'Waning gibbous moon'], [0.78, 'Last quarter moon'], [0.97, 'Waning crescent moon'], [2, 'New moon']];
      for (var q = 0; q < names.length; q++) {
        if (phase < names[q][0]) { if (moonName) moonName.textContent = names[q][1]; break; }
      }
    }

    var marks = dial.querySelectorAll('.mark');
    var rows = document.querySelectorAll('.nightlog li');
    /* A mark and its row share a data-i; the rows sit in two columns, so
       position in the page does not match the order of the night. */
    var pick = function (index) {
      for (var i = 0; i < marks.length; i++) marks[i].classList.toggle('is-on', marks[i].getAttribute('data-i') === index);
      for (var j = 0; j < rows.length; j++) rows[j].classList.toggle('is-on', rows[j].getAttribute('data-i') === index);
    };
    var pair = function (el) {
      var index = el.getAttribute('data-i');
      el.addEventListener('click', function () { pick(index); });
      el.addEventListener('pointerenter', function (e) { if (e.pointerType === 'mouse') pick(index); });
    };
    for (var k = 0; k < marks.length; k++) pair(marks[k]);
    for (var r = 0; r < rows.length; r++) pair(rows[r]);
  }

  /* The mark in the header keeps time with the page: midnight at the top,
     morning by the end. */
  var orbit = document.querySelector('.orbit');
  if (orbit && !calm) {
    var queued = false;
    var turn = function () {
      queued = false;
      var max = root.scrollHeight - window.innerHeight;
      var part = max > 0 ? Math.min(1, Math.max(0, window.pageYOffset / max)) : 0;
      orbit.style.transform = 'rotate(' + (part * 240).toFixed(1) + 'deg)';
    };
    window.addEventListener('scroll', function () {
      if (!queued) { queued = true; window.requestAnimationFrame(turn); }
    }, { passive: true });
    turn();
  }

  /* The morning queue. */
  var cards = document.querySelector('.cards');
  var record = document.querySelector('.record ol');
  var reset = document.getElementById('queue-reset');
  if (cards && record && reset) {
    /* The upper small dial on the hero counts what is still waiting here. */
    var countDial = document.querySelector('.dial-count');
    var countNote = document.getElementById('queue-count');
    var recount = function () {
      var left = cards.querySelectorAll('.card:not(.is-done)').length;
      if (countDial) countDial.textContent = left;
      if (countNote) countNote.textContent = left === 0 ? 'Nothing waiting for sign-off' : left + ' waiting for sign-off';
    };
    /* The figure at the top of the page follows the approvals: the proposal
       gives way to an amber route into the folder that was chosen. */
    var routes = document.querySelector('.routes');
    var route = function (doc, folder) {
      if (!routes) return;
      var parts = routes.querySelectorAll('[data-doc]');
      for (var i = 0; i < parts.length; i++) {
        var part = parts[i];
        if (doc === null) { part.classList.remove('is-off', 'is-done', 'is-on'); continue; }
        if (part.getAttribute('data-doc') !== doc) continue;
        if (part.classList.contains('proposal')) part.classList.add('is-off');
        if (part.classList.contains('wait')) part.classList.add('is-done');
        if (part.classList.contains('filed')) part.classList.toggle('is-on', part.getAttribute('data-folder') === folder);
      }
      var on = routes.querySelectorAll('.filed.is-on'), dests = routes.querySelectorAll('.dest');
      for (var j = 0; j < dests.length; j++) {
        var lit = false;
        for (var k = 0; k < on.length; k++) if (on[k].getAttribute('data-folder') === dests[j].getAttribute('data-folder')) lit = true;
        dests[j].classList.toggle('is-filed', lit);
      }
    };
    cards.addEventListener('click', function (e) {
      var btn = e.target.closest ? e.target.closest('button[data-act]') : null;
      if (!btn) return;
      var card = btn.closest('.card');
      var shown = card.querySelector('.folder');
      var choice = card.querySelector('select');
      if (btn.getAttribute('data-act') === 'change') {
        shown.hidden = true;
        choice.hidden = false;
        btn.hidden = true;
        choice.focus();
        return;
      }
      var proposed = card.getAttribute('data-folder');
      var folder = choice.hidden ? proposed : choice.value;
      var now = clock(new Date());
      shown.textContent = folder;
      shown.hidden = false;
      choice.hidden = true;
      card.classList.add('is-done');
      card.querySelector('.card-actions').hidden = true;
      var stamp = card.querySelector('.approved');
      stamp.querySelector('b').textContent = now;
      stamp.hidden = false;

      var row = document.createElement('li');
      row.className = 'by-person added';
      var when = document.createElement('time');
      when.textContent = now;
      var what = document.createElement('p');
      what.textContent = folder === proposed
        ? 'You approved filing ' + card.getAttribute('data-doc') + ' to ' + folder + '.'
        : 'You changed the folder to ' + folder + ' and approved. The correction is kept as a rule for next time.';
      row.appendChild(when);
      row.appendChild(what);
      record.appendChild(row);
      reset.hidden = false;
      recount();
      route(card.getAttribute('data-doc'), folder);
    });

    reset.addEventListener('click', function () {
      var all = cards.querySelectorAll('.card');
      for (var i = 0; i < all.length; i++) {
        var card = all[i], proposed = card.getAttribute('data-folder');
        var shown = card.querySelector('.folder'), choice = card.querySelector('select');
        shown.textContent = proposed;
        shown.hidden = false;
        choice.value = proposed;
        choice.hidden = true;
        card.classList.remove('is-done');
        card.querySelector('.card-actions').hidden = false;
        card.querySelector('[data-act="change"]').hidden = false;
        card.querySelector('.approved').hidden = true;
      }
      var added = record.querySelectorAll('.added');
      for (var j = 0; j < added.length; j++) record.removeChild(added[j]);
      reset.hidden = true;
      recount();
      route(null);
    });
  }

  /* The scope gate. Anything it cannot read is blocked. */
  var form = document.getElementById('gate-form');
  var entry = document.getElementById('gate-input');
  var verdict = document.getElementById('gate-verdict');
  if (form && entry && verdict) {
    var ip4 = function (text) {
      var m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(text);
      if (!m) return null;
      var n = 0;
      for (var i = 1; i <= 4; i++) {
        var octet = parseInt(m[i], 10);
        if (octet > 255) return null;
        n = n * 256 + octet;
      }
      return n;
    };
    var dotted = function (n) {
      return [Math.floor(n / 16777216), Math.floor(n / 65536) % 256, Math.floor(n / 256) % 256, n % 256].join('.');
    };
    var hosts = ['app.example.com', 'api.example.com'];
    var netBase = ip4('10.20.0.0'), netSize = 256;
    var excluded = ip4('10.20.0.53');
    var hostname = /^(?=.{1,253}$)[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/;

    /* The map at the top of the page rings the cell the gate was asked about. */
    var map = document.querySelector('.scopemap');
    var say = function (state, text, mark) {
      verdict.setAttribute('data-state', state);
      if (map) {
        var old = map.querySelectorAll('.is-probe');
        for (var o = 0; o < old.length; o++) old[o].classList.remove('is-probe', 'is-allowed', 'is-blocked');
        var hit = mark ? map.querySelector('[data-mark="' + mark + '"]') : null;
        if (hit) hit.classList.add('is-probe', state === 'allowed' ? 'is-allowed' : 'is-blocked');
      }
      verdict.querySelector('strong').textContent = state === 'allowed' ? 'Allowed.' : 'Blocked.';
      verdict.querySelector('span').textContent = text;
    };
    var check = function (raw) {
      var target = String(raw).trim().toLowerCase()
        .replace(/^[a-z][a-z0-9+.-]*:\/\//, '')
        .replace(/[\/?#].*$/, '')
        .replace(/:\d+$/, '')
        .replace(/\.$/, '');
      if (!target) return say('blocked', 'Nothing was entered. Type a hostname or an IPv4 address, such as api.example.com or 10.20.0.14.');
      var address = ip4(target);
      if (address !== null) {
        var shown = dotted(address);
        if (address === excluded) return say('blocked', shown + ' is excluded by name in the authorization. The agent stops and the attempt is logged.', shown);
        if (address >= netBase && address < netBase + netSize) return say('allowed', shown + ' is inside 10.20.0.0/24, which the signed scope lists.', shown);
        return say('blocked', shown + ' is outside the signed scope. The agent never contacts it.', shown);
      }
      if (hostname.test(target)) {
        if (hosts.indexOf(target) !== -1) return say('allowed', target + ' is listed in the signed scope.', target);
        if (/(^|\.)example\.com$/.test(target)) return say('blocked', target + ' is not listed. A related name is not assumed to be in scope.');
        return say('blocked', target + ' is not in the signed scope. The agent never contacts it.');
      }
      return say('blocked', 'That is not a hostname or an IPv4 address. Anything the gate cannot read is blocked.');
    };

    form.addEventListener('submit', function (e) { e.preventDefault(); check(entry.value); });
    form.addEventListener('click', function (e) {
      var preset = e.target.closest ? e.target.closest('button[data-target]') : null;
      if (!preset) return;
      entry.value = preset.getAttribute('data-target');
      check(entry.value);
    });
    check(entry.value);
  }
})();

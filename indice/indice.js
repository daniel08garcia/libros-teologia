(() => {
  "use strict";
  const datos = JSON.parse(document.getElementById("catalogo").textContent);
  const root = document.documentElement;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hayVT = typeof document.startViewTransition === "function" && !reduce;
  if (hayVT) root.classList.add("con-vt");
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const esc = (s) =>
    String(s).replace(
      /[&<>"]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
    );
  const valorRomano = (s) => {
    const v = { I: 1, V: 5, X: 10, L: 50, C: 100 };
    let r = 0,
      p = 0;
    for (const ch of [...s].reverse()) {
      const c = v[ch] || 0;
      r += c >= p ? c : -c;
      p = c;
    }
    return r;
  };
  const SIGLOS = [...new Set(datos.obras.map((o) => o.siglo))].sort(
    (a, b) => valorRomano(a) - valorRomano(b),
  );

  // Minúsculas para artículos y preposiciones en títulos escritos "En Mayúscula Cada Palabra"
  const MENORES = new Set(
    "a al ante bajo con contra de del desde e el en entre hacia hasta la las lo los o para por según sin sobre tras u un una unos unas y".split(
      " ",
    ),
  );
  const tc = (s) =>
    s
      .split(" ")
      .map((w, i, ws) => {
        if (i === 0 || /[:.]$/.test(ws[i - 1])) return w;
        return MENORES.has(w.toLowerCase().replace(/[,;]$/, ""))
          ? w.toLowerCase()
          : w;
      })
      .join(" ");
  const romano = (n) => {
    const t = [
      [1000, "M"],
      [900, "CM"],
      [500, "D"],
      [400, "CD"],
      [100, "C"],
      [90, "XC"],
      [50, "L"],
      [40, "XL"],
      [10, "X"],
      [9, "IX"],
      [5, "V"],
      [4, "IV"],
      [1, "I"],
    ];
    let r = "";
    for (const [v, s] of t)
      while (n >= v) {
        r += s;
        n -= v;
      }
    return r;
  };
  const lectura = (min) =>
    min < 60 ? `${min} min` : `${Math.round(min / 60)} h`;

  // Autores sin color en indice/autores.json: tono estable a partir del nombre, en la misma gama sobria
  const PALETA = [
    "#4a1f2a",
    "#1f3346",
    "#2f3d24",
    "#4b3420",
    "#33264a",
    "#203c3c",
    "#2c2c3e",
    "#3e3a1c",
    "#1c3a33",
    "#45283d",
    "#283a4a",
    "#3a2a1c",
  ];
  const colorDe = (s) => {
    let h = 0;
    for (const ch of s) h = (h * 31 + ch.codePointAt(0)) >>> 0;
    return PALETA[h % PALETA.length];
  };
  datos.obras.forEach((o, i) => {
    o.i = i;
    o.min = o.textos.reduce((s, t) => s + t.m, 0);
    o.color = o.color || colorDe(o.carpeta);
    o.grosor = Math.round(9 + Math.log2(o.textos.length + 1) * 2.4);
  });

  /* ───────── Rosetón ───────── */
  function construirRosa() {
    const TAU = Math.PI * 2,
      N = 12;
    const f = (v) => +v.toFixed(2);
    const P = (r, a) => [f(r * Math.cos(a)), f(r * Math.sin(a))];
    const C = (cx, cy, r) =>
      `M${f(cx - r)} ${f(cy)}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;
    const ang = (k) => (k / N) * TAU - TAU / 4;
    const A = [],
      B = [],
      Cc = [];
    // Capa exterior (fija, al fondo)
    A.push(C(0, 0, 492), C(0, 0, 481), C(0, 0, 438));
    for (let i = 0; i < 24; i++) {
      const a0 = (i / 24) * TAU,
        a1 = ((i + 1) / 24) * TAU,
        am = (a0 + a1) / 2;
      const [x0, y0] = P(438, a0),
        [x1, y1] = P(438, a1),
        [xm, ym] = P(489, am);
      A.push(`M${x0} ${y0}Q${xm} ${ym} ${x1} ${y1}`);
    }
    for (let i = 0; i < N; i++) {
      const a = ang(i + 0.5);
      const [x, y] = P(392, a);
      A.push(C(x, y, 40), C(x, y, 33));
      for (let k = 0; k < 4; k++) {
        const b = a + (k * TAU) / 4;
        A.push(C(f(x + 11 * Math.cos(b)), f(y + 11 * Math.sin(b)), 11));
      }
    }
    // Capa media (pétalos góticos, se mece)
    B.push(C(0, 0, 382));
    const petalo = (r0, r1, w, R, a) => {
      const [lx, ly] = P(r0, a - w),
        [tx, ty] = P(r1, a),
        [rx, ry] = P(r0, a + w);
      return `M${lx} ${ly}A${R} ${R} 0 0 1 ${tx} ${ty}A${R} ${R} 0 0 1 ${rx} ${ry}`;
    };
    const paso = TAU / N;
    for (let i = 0; i < N; i++) {
      const a = ang(i);
      B.push(petalo(150, 376, (paso / 2) * 0.93, 270, a));
      B.push(petalo(170, 342, (paso / 2) * 0.6, 225, a));
      const [cx, cy] = P(262, a);
      B.push(C(cx, cy, 15));
      for (let k = 0; k < 3; k++) {
        const b = a + (k * TAU) / 3;
        B.push(C(f(cx + 6.5 * Math.cos(b)), f(cy + 6.5 * Math.sin(b)), 6));
      }
      const s = ang(i + 0.5);
      const [ax, ay] = P(153, s),
        [bx, by] = P(352, s);
      B.push(`M${ax} ${ay}L${bx} ${by}`);
    }
    // Capa central (estrella {12/5}, gira en sentido contrario)
    Cc.push(C(0, 0, 150), C(0, 0, 140));
    let d = "";
    for (let k = 0; k <= N; k++) {
      const [x, y] = P(140, ang((k * 5) % N));
      d += (k ? "L" : "M") + x + " " + y;
    }
    Cc.push(d, C(0, 0, 36.2), C(0, 0, 10));
    const capa = (cls, paths, base, paso) =>
      `<svg class="${cls}" viewBox="-500 -500 1000 1000">${paths.map((p, i) => `<path pathLength="1" d="${p}" style="--d:${(base + i * paso).toFixed(3)}s"/>`).join("")}</svg>`;
    $("#rosa3d").insertAdjacentHTML(
      "beforeend",
      capa("capa-a", A, 0.2, 0.012) +
        capa("capa-b", B, 0.55, 0.02) +
        capa("capa-c", Cc, 1.1, 0.12),
    );
  }
  construirRosa();

  /* ───────── Portada: letras, cifras, inclinación y scroll ───────── */
  let n = 0;
  $$("#titulo .l").forEach((l) => {
    l.innerHTML = [...l.textContent]
      .map((ch) =>
        ch === " " ? " " : `<span class="ch" style="--i:${n++}">${ch}</span>`,
      )
      .join("");
  });
  $("#titulo").setAttribute("aria-label", "Nube de Testigos");
  requestAnimationFrame(() =>
    setTimeout(() => $("#orla-hero").classList.add("in"), 900),
  );

  const siglos = new Set(datos.obras.map((o) => o.siglo)).size;
  const cifras = [
    [datos.total, "textos"],
    [datos.obras.length, "obras"],
    [siglos, "siglos"],
  ];
  $("#cifras").innerHTML = cifras
    .map(([v, l]) => `<span><b data-n="${v}">${reduce ? v : 0}</b>${l}</span>`)
    .join("");
  if (!reduce)
    setTimeout(() => {
      const t0 = performance.now();
      const tick = (t) => {
        const k = Math.min(1, (t - t0) / 1800),
          e = 1 - Math.pow(1 - k, 4);
        $$("#cifras b").forEach(
          (b) => (b.textContent = Math.round(+b.dataset.n * e)),
        );
        if (k < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, 1600);

  const hero = $(".hero"),
    rosa3d = $("#rosa3d"),
    top = $("#top");
  let objX = 0,
    objY = 0,
    curX = 0,
    curY = 0,
    puntero = false,
    heroVisible = true;
  addEventListener(
    "pointermove",
    (e) => {
      if (e.pointerType !== "mouse") return;
      puntero = true;
      objY = (e.clientX / innerWidth - 0.5) * 14;
      objX = (e.clientY / innerHeight - 0.5) * -11;
    },
    { passive: true },
  );
  function bucle(t) {
    if (heroVisible && !reduce) {
      const x = puntero ? objX : Math.cos(t / 9000) * 4;
      const y = puntero ? objY : Math.sin(t / 7000) * 6;
      curX += (x - curX) * 0.045;
      curY += (y - curY) * 0.045;
      rosa3d.style.setProperty("--tx", curX.toFixed(3) + "deg");
      rosa3d.style.setProperty("--ty", curY.toFixed(3) + "deg");
    }
    requestAnimationFrame(bucle);
  }
  requestAnimationFrame(bucle);
  new IntersectionObserver(([e]) => (heroVisible = e.isIntersecting)).observe(
    hero,
  );
  function alDesplazar() {
    const p = Math.min(1, Math.max(0, scrollY / innerHeight));
    hero.style.setProperty("--p", p.toFixed(4));
    top.classList.toggle("solida", scrollY > 30);
    top.classList.toggle("titulo-visible", scrollY > innerHeight * 0.45);
  }
  addEventListener("scroll", () => requestAnimationFrame(alDesplazar), {
    passive: true,
  });
  alDesplazar();

  /* ───────── Aparición al desplazar ───────── */
  const io = new IntersectionObserver(
    (es) =>
      es.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      }),
    { rootMargin: "0px 0px -8% 0px", threshold: 0.1 },
  );

  /* ───────── Portadas ───────── */
  function tapa(o) {
    const k = o.serie || `siglo ${o.siglo.toLowerCase()}`;
    const vol = o.volumen
      ? `<span class="vol">${romano(+o.volumen)}</span>`
      : "";
    const titulo = tc(o.titulo);
    return `<div class="tapa${titulo.length > 34 ? " largo" : ""}" style="--c:${o.color}"><div class="in">
      <div class="k">${esc(k.toLowerCase())}${vol}</div>
      <div class="tt">${esc(titulo)}<svg class="fl" aria-hidden="true"><use href="#flor"/></svg></div>
      <div class="au">${esc(o.autor.toLowerCase())}<span class="an">${esc(o.anio)}</span></div>
    </div><span class="brillo"></span></div>`;
  }

  const estante = $("#estante");
  let html = "";
  for (const s of SIGLOS) {
    const suyas = datos.obras.filter((o) => o.siglo === s);
    if (!suyas.length) continue;
    html += `<div class="grupo" data-siglo="${s}"><div class="divisor"><span>siglo <b>${s.toLowerCase()}</b></span></div><div class="fila">`;
    suyas.forEach((o, col) => {
      html += `<article class="obra" data-i="${o.i}" style="--d:${(col % 5) * 80}ms">
      <button class="libro" style="--t:${o.grosor}px" aria-label="${esc(tc(o.titulo) + ", " + o.autor)}">${tapa(o)}<span class="cantos" aria-hidden="true"></span></button>
      <div class="pie"><b>${o.textos.length}</b> ${o.textos.length === 1 ? "texto" : "textos"} · ${lectura(o.min)}</div>
    </article>`;
    });
    html += `</div></div>`;
  }
  estante.innerHTML = html;
  const tarjetas = $$(".obra", estante),
    divisores = $$(".divisor", estante),
    grupos = $$(".grupo", estante);
  [...tarjetas, ...divisores].forEach((el) => io.observe(el));
  $$(".cab, .epigrafe, .colofon").forEach((el) => io.observe(el));

  // Inclinación 3D sutil siguiendo el cursor
  function inclinar(el, { base = 0, ampY = 10, ampX = 8, brillo = false }) {
    el.addEventListener("pointermove", (e) => {
      if (e.pointerType !== "mouse" || reduce) return;
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width,
        y = (e.clientY - r.top) / r.height;
      el.classList.add("mueve");
      el.style.setProperty(
        "--ry",
        `${(base + (x - 0.5) * ampY).toFixed(2)}deg`,
      );
      el.style.setProperty("--rx", `${((0.5 - y) * ampX).toFixed(2)}deg`);
      if (brillo) {
        el.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
        el.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
      }
    });
    el.addEventListener("pointerleave", () => {
      el.classList.remove("mueve");
      el.style.removeProperty("--ry");
      el.style.removeProperty("--rx");
    });
  }
  $$(".libro", estante).forEach((l) =>
    inclinar(l, { base: -21, ampY: 10, ampX: 7, brillo: true }),
  );

  /* ───────── Filtros ───────── */
  const filtro = { siglo: "todos", autor: null };
  const filtros = $("#filtros");
  function pintarFiltros() {
    const presentes = SIGLOS.filter((s) =>
      datos.obras.some((o) => o.siglo === s),
    );
    let h = `<button class="chip" data-siglo="todos" aria-pressed="${!filtro.autor && filtro.siglo === "todos"}">todos</button>`;
    h += presentes
      .map(
        (s) =>
          `<button class="chip" data-siglo="${s}" aria-pressed="${!filtro.autor && filtro.siglo === s}">${s.toLowerCase()}</button>`,
      )
      .join("");
    if (filtro.autor) {
      const a = datos.autores.find((x) => x.carpeta === filtro.autor);
      h += `<button class="chip" data-quitar aria-pressed="true" aria-label="Quitar filtro ${esc(a.nombre)}">${esc(a.nombre.toLowerCase())}<span class="x" aria-hidden="true">×</span></button>`;
    }
    filtros.innerHTML =
      h + `<span class="indicador" aria-hidden="true"></span>`;
    moverIndicador();
  }
  function moverIndicador() {
    const b = $('.chip[aria-pressed="true"]', filtros),
      ind = $(".indicador", filtros);
    if (!b || !ind) return;
    ind.style.width = `${b.offsetWidth - 28}px`;
    ind.style.translate = `${b.offsetLeft + 14}px ${b.offsetTop + b.offsetHeight - 4}px`;
  }
  function aplicarFiltro() {
    const visibles = new Set();
    tarjetas.forEach((c) => {
      const o = datos.obras[c.dataset.i];
      const ok =
        (filtro.siglo === "todos" || o.siglo === filtro.siglo) &&
        (!filtro.autor || o.carpeta === filtro.autor);
      c.hidden = !ok;
      if (ok) {
        c.classList.add("in");
        visibles.add(o.siglo);
      }
    });
    grupos.forEach((g) => {
      g.hidden = !visibles.has(g.dataset.siglo);
      $(".divisor", g).classList.add("in");
    });
  }
  function cambiarFiltro(cambio) {
    const actualizar = () => {
      cambio();
      pintarFiltros();
      aplicarFiltro();
    };
    if (!hayVT) return actualizar();
    [...tarjetas, ...divisores].forEach(
      (el, i) => (el.style.viewTransitionName = `e${i}`),
    );
    root.classList.add("vt-activa");
    const t = document.startViewTransition(actualizar);
    t.finished.finally(() => {
      [...tarjetas, ...divisores].forEach(
        (el) => (el.style.viewTransitionName = ""),
      );
      root.classList.remove("vt-activa");
    });
  }
  filtros.addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (!b) return;
    if (b.hasAttribute("data-quitar"))
      cambiarFiltro(() => (filtro.autor = null));
    else
      cambiarFiltro(() => {
        filtro.siglo = b.dataset.siglo;
        filtro.autor = null;
      });
  });
  pintarFiltros();
  addEventListener("resize", moverIndicador);
  document.fonts?.ready.then(moverIndicador);

  /* ───────── Epígrafe ───────── */
  const cita = $("#cita");
  cita.innerHTML = cita.textContent
    .split(" ")
    .map((w, i) => `<span class="w" style="--i:${i}">${esc(w)}</span>`)
    .join(" ");

  /* ───────── Autores ───────── */
  // Monograma: ignora partículas (Tomás de Aquino → TA; Ireneo → I)
  const PARTICULAS = new Set([
    "de",
    "del",
    "la",
    "of",
    "von",
    "van",
    "der",
    "y",
  ]);
  const iniciales = (nom) => {
    const p = nom
      .replace(/\./g, "")
      .split(/\s+/)
      .filter((w) => !PARTICULAS.has(w.toLowerCase()));
    return p.length > 1 ? p[0][0] + p.at(-1)[0] : p[0][0];
  };
  $("#lista-autores").innerHTML = datos.autores
    .map((a, i) => {
      const varios = a.coleccion;
      const cnt = varios
        ? `${a.obras} ${a.obras === 1 ? "volumen" : "volúmenes"} · ${a.predicadores} autores`
        : `${a.textos} ${a.textos === 1 ? "texto" : "textos"} · ${a.obras} ${a.obras === 1 ? "obra" : "obras"}`;
      return `<button class="autor" data-carpeta="${esc(a.carpeta)}" style="--d:${(i % 5) * 80}ms">
      <span class="medalla">
        <svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="49" stroke-width=".6" vector-effect="non-scaling-stroke" opacity=".8"/></svg>
        <svg class="anillo" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="45.5" stroke-width="2.4" stroke-dasharray=".5 3.07" opacity=".55"/></svg>
        <span class="mono${a.monograma ? " or" : ""}">${esc(a.monograma || iniciales(a.nombre))}</span>
      </span>
      <span class="sg">siglo ${a.siglo.toLowerCase()}</span>
      <span class="nom">${esc(a.nombre)}</span>
      <span class="vida">${esc(a.vida)}</span>
      <span class="cnt">${cnt}</span>
    </button>`;
    })
    .join("");
  $$(".autor").forEach((el) => {
    io.observe(el);
    inclinar($(".medalla", el), { ampY: 16, ampX: 16 });
  });
  $("#lista-autores").addEventListener("click", (e) => {
    const b = e.target.closest(".autor");
    if (!b) return;
    const carpeta = b.dataset.carpeta;
    $("#obras").scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
    let hecho = false;
    const aplicar = () => {
      if (hecho) return;
      hecho = true;
      cambiarFiltro(() => {
        filtro.autor = carpeta;
        filtro.siglo = "todos";
      });
    };
    if ("onscrollend" in window)
      addEventListener("scrollend", aplicar, { once: true });
    setTimeout(aplicar, 900);
  });

  /* ───────── Ficha de obra ───────── */
  const ficha = $("#ficha");
  let abierta = null;
  function htmlFicha(o) {
    const k = o.serie || `siglo ${o.siglo.toLowerCase()}`;
    const items = o.textos
      .map((t, i) => {
        const num = t.n === "0" ? "pref." : t.n.toLowerCase();
        const sub = [t.a, t.o].filter(Boolean).map(esc).join(" · ");
        return `<li style="--i:${i}"><a href="${esc(t.h)}"><span class="num">${num}</span><span><span class="t">${esc(tc(t.t))}</span>${sub ? `<span class="s">${sub}</span>` : ""}</span><span class="min">${t.m} min</span></a></li>`;
      })
      .join("");
    return `<div class="ficha-izq">
        <div class="libro-f">${tapa(o)}</div>
        <dl class="datos">
          <div><dt>textos</dt><dd>${o.textos.length}</dd></div>
          <div><dt>lectura</dt><dd>${lectura(o.min)}</dd></div>
          <div><dt>publicación</dt><dd>${esc(o.anio)}</dd></div>
          <div><dt>siglo</dt><dd>${o.siglo}</dd></div>
        </dl>
        <a class="cta" href="${esc(o.textos[0].h)}">comenzar a leer<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M14 7l5 5-5 5"/></svg></a>
      </div>
      <div class="ficha-der">
        <button class="icon-btn cerrar" aria-label="Cerrar"><svg class="ico" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        <p class="k">${esc(k.toLowerCase())}${o.volumen ? ` · volumen ${romano(+o.volumen).toLowerCase()}` : ""}</p>
        <h3 id="ficha-titulo">${esc(tc(o.titulo))}</h3>
        <p class="meta">${esc(o.autor.toLowerCase())}</p>
        <div class="orla in"><svg aria-hidden="true"><use href="#flor"/></svg></div>
        <ol class="indice">${items}</ol>
      </div>`;
  }
  function abrirFicha(i, libro) {
    const o = datos.obras[i];
    const pintar = () => {
      ficha.innerHTML = htmlFicha(o);
      if (!ficha.open) ficha.showModal();
      $(".ficha-der", ficha).scrollTop = 0;
    };
    abierta = { libro };
    // Enlace directo a la ficha: index.html#obra-<id>
    history.replaceState(null, "", `#obra-${o.id}`);
    if (!hayVT || !libro) return pintar();
    const tg = $(".tapa", libro);
    tg.style.viewTransitionName = "portada";
    const t = document.startViewTransition(() => {
      tg.style.viewTransitionName = "";
      pintar();
      $(".tapa", ficha).style.viewTransitionName = "portada";
    });
    t.finished.finally(() => {
      const tf = $(".tapa", ficha);
      if (tf) tf.style.viewTransitionName = "";
    });
  }
  function cerrarFicha() {
    const libro = abierta?.libro;
    if (!hayVT || !libro || libro.closest("[hidden]")) {
      ficha.close();
      return;
    }
    const tf = $(".tapa", ficha),
      tg = $(".tapa", libro);
    tf.style.viewTransitionName = "portada";
    const t = document.startViewTransition(() => {
      tf.style.viewTransitionName = "";
      ficha.close();
      tg.style.viewTransitionName = "portada";
    });
    t.finished.finally(() => (tg.style.viewTransitionName = ""));
  }
  estante.addEventListener("click", (e) => {
    const l = e.target.closest(".libro");
    if (l) abrirFicha(+l.closest(".obra").dataset.i, l);
  });
  ficha.addEventListener("cancel", (e) => {
    e.preventDefault();
    cerrarFicha();
  });
  ficha.addEventListener("click", (e) => {
    if (e.target === ficha || e.target.closest(".cerrar")) cerrarFicha();
  });
  ficha.addEventListener("close", () => {
    if (location.hash.startsWith("#obra-"))
      history.replaceState(null, "", location.pathname + location.search);
  });
  // Abrir la ficha si se llega con un enlace directo
  function abrirDesdeEnlace() {
    const id = decodeURIComponent(location.hash.slice(1)).replace(/^obra-/, "");
    const i = datos.obras.findIndex((o) => o.id === id);
    if (i < 0 || !location.hash.startsWith("#obra-")) return;
    const libro = $(`.obra[data-i="${i}"] .libro`, estante);
    abrirFicha(i, null);
    abierta = { libro };
  }
  abrirDesdeEnlace();
  addEventListener("hashchange", abrirDesdeEnlace);

  /* ───────── Buscador (prototipo: títulos, autores y obras) ───────── */
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const indice = [];
  datos.obras.forEach((o) =>
    o.textos.forEach((t) => {
      const titulo = tc(t.t);
      indice.push({
        o,
        t,
        titulo,
        tit: norm(titulo),
        todo: norm([titulo, t.o, t.a, o.autor, o.titulo, o.serie].join(" ")),
      });
    }),
  );
  const q = $("#q"),
    res = $("#resultados");
  let sel = -1,
    actuales = [];
  function resaltar(texto, toks) {
    const n = norm(texto);
    if (n.length !== texto.length) return esc(texto);
    const marcas = new Array(texto.length).fill(false);
    for (const k of toks) {
      let p = n.indexOf(k);
      while (p !== -1) {
        for (let j = p; j < p + k.length; j++) marcas[j] = true;
        p = n.indexOf(k, p + k.length);
      }
    }
    let out = "",
      dentro = false;
    for (let j = 0; j < texto.length; j++) {
      if (marcas[j] && !dentro) {
        out += "<mark>";
        dentro = true;
      }
      if (!marcas[j] && dentro) {
        out += "</mark>";
        dentro = false;
      }
      out += esc(texto[j]);
    }
    return out + (dentro ? "</mark>" : "");
  }
  function buscar() {
    const toks = norm(q.value)
      .split(/\s+/)
      .filter((k) => k.length > 1);
    if (!toks.length) {
      cerrarResultados();
      return;
    }
    const hallados = [];
    for (const it of indice) {
      if (!toks.every((k) => it.todo.includes(k))) continue;
      let s = 0;
      for (const k of toks) {
        if (it.tit.includes(k)) s += 2;
        if (it.tit.startsWith(k)) s += 1;
      }
      hallados.push([s, it]);
    }
    hallados.sort((a, b) => b[0] - a[0]);
    actuales = hallados.slice(0, 8).map((x) => x[1]);
    sel = -1;
    const nota = `<div class="nota">${hallados.length} ${hallados.length === 1 ? "coincidencia" : "coincidencias"} en títulos y autores.</div>`;
    res.innerHTML = actuales.length
      ? actuales
          .map((it, i) => {
            const num = it.t.n === "0" ? "pref." : it.t.n.toLowerCase();
            const meta = [it.t.a || it.o.autor, tc(it.o.titulo)].join(" · ");
            return `<a class="res" role="option" id="r${i}" href="${esc(it.t.h)}" style="--i:${i}"><span class="num">${num}</span><span class="t">${resaltar(it.titulo, toks)}</span><span class="m">${esc(meta)}</span></a>`;
          })
          .join("") + nota
      : `<div class="vacio">Ningún título coincide con «${esc(q.value.trim())}».</div>`;
    res.classList.add("abierto");
    q.setAttribute("aria-expanded", "true");
  }
  function cerrarResultados() {
    res.classList.remove("abierto");
    q.setAttribute("aria-expanded", "false");
    q.removeAttribute("aria-activedescendant");
  }
  function marcarSel() {
    $$(".res", res).forEach((r, i) =>
      r.setAttribute("aria-selected", i === sel),
    );
    if (sel >= 0) {
      q.setAttribute("aria-activedescendant", `r${sel}`);
      $(`#r${sel}`).scrollIntoView({ block: "nearest" });
    }
  }
  q.addEventListener("input", buscar);
  q.addEventListener("focus", () => q.value.trim() && buscar());
  q.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && actuales.length) {
      sel = (sel + 1) % actuales.length;
      marcarSel();
      e.preventDefault();
    } else if (e.key === "ArrowUp" && actuales.length) {
      sel = (sel - 1 + actuales.length) % actuales.length;
      marcarSel();
      e.preventDefault();
    } else if (e.key === "Enter" && actuales.length) {
      location.href = actuales[Math.max(sel, 0)].t.h;
    } else if (e.key === "Escape") {
      q.value = "";
      cerrarResultados();
      q.blur();
    }
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".buscar")) cerrarResultados();
  });
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "/" &&
      !/input|textarea/i.test(document.activeElement?.tagName) &&
      !ficha.open
    ) {
      e.preventDefault();
      q.focus();
    }
  });
  $("#ir-buscar").addEventListener("click", () => {
    scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    setTimeout(() => q.focus({ preventScroll: true }), reduce ? 0 : 650);
  });

  /* ───────── Tema claro / oscuro con revelado circular ───────── */
  const temaActual = () =>
    root.dataset.theme ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  $("#tema").addEventListener("click", (e) => {
    const siguiente = temaActual() === "dark" ? "light" : "dark";
    const aplicar = () => {
      root.dataset.theme = siguiente;
      try {
        localStorage.setItem("tema", siguiente);
      } catch (err) {}
    };
    if (!hayVT) return aplicar();
    const x = e.clientX || innerWidth - 40,
      y = e.clientY || 33;
    const r = Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y),
    );
    root.classList.add("vt-tema");
    const t = document.startViewTransition(aplicar);
    t.ready.then(() =>
      root.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${r}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 950,
          easing: "cubic-bezier(.65,0,.35,1)",
          pseudoElement: "::view-transition-new(root)",
        },
      ),
    );
    t.finished.finally(() => root.classList.remove("vt-tema"));
  });
})();

/**
 * Registro rápido: autocompletado, estadísticas, temporizador, historial, drag&drop.
 */
(function () {
    var U = window.REGISTRO_RAPIDO_URLS || {};
    var modo = window.MODO_REGISTRO || 'quick';

    function postJson(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body || {}),
            credentials: 'same-origin',
        }).then(function (r) {
            return r.json();
        });
    }

    function notificarExterno(titulo, cuerpo) {
        if (typeof window.notificarApp === 'function') {
            window.notificarApp(titulo, cuerpo);
        } else if ('Notification' in window && Notification.permission === 'granted') {
            try {
                new Notification(titulo, { body: cuerpo, tag: 'gestion-horas' });
            } catch (e) {}
        }
    }

    function pedirPermisoNotif() {
        if (!('Notification' in window) || Notification.permission !== 'default') return;
        Notification.requestPermission();
    }

    /* --- Estadísticas hoy + alerta 8h (una vez por sesión) --- */
    var alerta8hMostrada = false;
    function actualizarStats() {
        if (!U.estadisticasHoy) return;
        fetch(U.estadisticasHoy, { credentials: 'same-origin' })
            .then(function (r) {
                return r.json();
            })
            .then(function (d) {
                var elH = document.getElementById('horas-hoy-stat');
                var elC = document.getElementById('cliente-top-stat');
                if (elH) elH.textContent = d.horas_hoy + 'h';
                if (elC) elC.textContent = d.cliente_top || '—';
                var sk = 'alerta8h_' + new Date().toISOString().slice(0, 10);
                if (d.alerta_8h && !alerta8hMostrada && sessionStorage.getItem(sk) !== '1') {
                    alerta8hMostrada = true;
                    sessionStorage.setItem(sk, '1');
                    notificarExterno('Horas del día', 'Has superado las 8 horas registradas hoy.');
                }
            });
    }

    /* --- Autocompletado clientes --- */
    function initAutocomplete() {
        var inp = document.getElementById('cliente_buscar');
        var hid = document.getElementById('cliente_id_hidden');
        var ul = document.getElementById('cliente_sugerencias');
        if (!inp || !hid || !ul || !U.buscarClientes) return;

        var tmr;
        function render(items) {
            ul.innerHTML = '';
            if (!items.length) {
                ul.style.display = 'none';
                return;
            }
            items.forEach(function (it) {
                var li = document.createElement('li');
                li.textContent = it.nombre + ' (' + it.horas_mes + 'h este mes)';
                li.addEventListener('click', function () {
                    hid.value = it.id;
                    inp.value = it.nombre;
                    ul.style.display = 'none';
                });
                ul.appendChild(li);
            });
            ul.style.display = 'block';
        }

        inp.addEventListener('input', function () {
            clearTimeout(tmr);
            var q = inp.value.trim();
            if (q.length < 2) {
                ul.style.display = 'none';
                return;
            }
            tmr = setTimeout(function () {
                fetch(U.buscarClientes + '?q=' + encodeURIComponent(q), { credentials: 'same-origin' })
                    .then(function (r) {
                        return r.json();
                    })
                    .then(render);
            }, 200);
        });

        document.addEventListener('click', function (e) {
            if (!inp.contains(e.target) && !ul.contains(e.target)) ul.style.display = 'none';
        });
    }

    /* --- Plantillas --- */
    function initPlantillas() {
        var sel = document.getElementById('sel_plantilla');
        var btn = document.getElementById('btn_aplicar_plantilla');
        if (!sel || !btn) return;
        btn.addEventListener('click', function () {
            var opt = sel.options[sel.selectedIndex];
            if (!opt || !opt.value) return;
            var hid = document.getElementById('cliente_id_hidden');
            var cinp = document.getElementById('cliente_buscar');
            var tsel = document.getElementById('tarea_id');
            var hc = document.getElementById('horas_custom');
            var obs = document.getElementById('observaciones');
            if (hid) hid.value = opt.getAttribute('data-cliente') || '';
            if (tsel) tsel.value = opt.getAttribute('data-tarea') || '';
            if (hc) hc.value = opt.getAttribute('data-horas') || '';
            if (obs) obs.value = opt.getAttribute('data-desc') || '';
            var cn = opt.textContent.split('(')[0].trim();
            if (cinp) cinp.value = cn;
        });
    }

    /* --- Historial --- */
    function cargarHistorial() {
        if (!U.historial) return;
        var per = document.getElementById('filtro-periodo');
        var cli = document.getElementById('filtro-cliente-hist');
        var tb = document.getElementById('tabla-historial-body');
        if (!per || !tb) return;
        var url = U.historial + '?periodo=' + encodeURIComponent(per.value);
        if (cli && cli.value) url += '&cliente_id=' + encodeURIComponent(cli.value);
        fetch(url, { credentials: 'same-origin' })
            .then(function (r) {
                return r.json();
            })
            .then(function (d) {
                tb.innerHTML = '';
                (d.registros || []).forEach(function (row) {
                    var tr = document.createElement('tr');
                    tr.innerHTML =
                        '<td>' +
                        row.fecha +
                        '</td><td>' +
                        escapeHtml(row.cliente) +
                        '</td><td>' +
                        escapeHtml(row.tarea) +
                        '</td><td>' +
                        row.horas +
                        '</td><td>' +
                        escapeHtml(row.observaciones || '') +
                        '</td>';
                    tb.appendChild(tr);
                });
            });
    }

    function escapeHtml(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    /* --- Temporizador --- */
    function initTimer() {
        var startBtn = document.getElementById('btn_timer_start');
        if (!startBtn || !U.timerEstado) return;

        var modal = document.getElementById('modal-finalizar-timer');
        var tiempoExactoEl = document.getElementById('tiempo-exacto-modal');
        var ultimoSegundos = 0;

        function fmtSeg(seg) {
            var h = Math.floor(seg / 3600);
            var m = Math.floor((seg % 3600) / 60);
            var s = seg % 60;
            return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        }

        function refreshTimerUi() {
            fetch(U.timerEstado, { credentials: 'same-origin' })
                .then(function (r) {
                    return r.json();
                })
                .then(function (d) {
                    var disp = document.getElementById('timer_display');
                    var ps = document.getElementById('btn_timer_pause');
                    var rs = document.getElementById('btn_timer_resume');
                    var st = document.getElementById('btn_timer_stop');
                    var ca = document.getElementById('btn_timer_cancel');
                    if (!d.activo) {
                        if (disp) {
                            disp.textContent = '';
                            disp.classList.remove('timer-corriendo');
                        }
                        startBtn.style.display = '';
                        if (ps) ps.style.display = 'none';
                        if (rs) rs.style.display = 'none';
                        if (st) st.style.display = 'none';
                        if (ca) ca.style.display = 'none';
                        return;
                    }
                    ultimoSegundos = d.segundos || 0;
                    startBtn.style.display = 'none';
                    if (disp) {
                        disp.textContent = (d.cliente || '') + ' — ' + (d.tarea || '') + ' — ' + d.texto + (d.pausado ? ' (pausa)' : '');
                        disp.classList.toggle('timer-corriendo', !d.pausado);
                    }
                    if (ps) ps.style.display = d.pausado ? 'none' : '';
                    if (rs) rs.style.display = d.pausado ? '' : 'none';
                    if (st) st.style.display = '';
                    if (ca) ca.style.display = '';
                });
        }

        startBtn.addEventListener('click', function () {
            var c = document.getElementById('timer_cliente').value;
            var t = document.getElementById('timer_tarea').value;
            var n = document.getElementById('timer_nota').value;
            if (!c || !t) {
                alert('Elige cliente y tarea');
                return;
            }
            postJson(U.timerIniciar, { cliente_id: parseInt(c, 10), tarea_id: parseInt(t, 10), nota: n }).then(function (r) {
                if (!r.ok) alert(r.error || 'Error');
                refreshTimerUi();
            });
        });
        var pauseBtn = document.getElementById('btn_timer_pause');
        if (pauseBtn) pauseBtn.addEventListener('click', function () {
            postJson(U.timerPausar, {}).then(refreshTimerUi);
        });
        var resumeBtn = document.getElementById('btn_timer_resume');
        if (resumeBtn) resumeBtn.addEventListener('click', function () {
            postJson(U.timerReanudar, {}).then(refreshTimerUi);
        });
        var cancelBtn = document.getElementById('btn_timer_cancel');
        if (cancelBtn)
            cancelBtn.addEventListener('click', function () {
                if (!confirm('¿Descartar el temporizador sin guardar?')) return;
                postJson(U.timerCancelar, {}).then(refreshTimerUi);
            });

        var stopBtn = document.getElementById('btn_timer_stop');
        if (stopBtn)
            stopBtn.addEventListener('click', function () {
                if (tiempoExactoEl) tiempoExactoEl.textContent = fmtSeg(ultimoSegundos);
                if (modal) modal.style.display = 'flex';
            });

        var cerrarM = document.getElementById('btn_cerrar_modal_timer');
        if (cerrarM)
            cerrarM.addEventListener('click', function () {
                if (modal) modal.style.display = 'none';
            });

        document.querySelectorAll('#modal-finalizar-timer .btn-tiempo[data-r]').forEach(function (b) {
            b.addEventListener('click', function () {
                var r = b.getAttribute('data-r');
                postJson(U.timerFinalizar, { redondeo: r || null }).then(function (res) {
                    if (!res.ok) {
                        alert(res.error || 'Error');
                        return;
                    }
                    if (modal) modal.style.display = 'none';
                    notificarExterno('Temporizador', 'Guardado: ' + (res.horas || '') + ' h. Total hoy: ' + (res.horas_hoy || '') + ' h');
                    if (res.alerta_8h) notificarExterno('Aviso de horas', 'Llevas más de 8 h registradas hoy.');
                    refreshTimerUi();
                    actualizarStats();
                    cargarHistorial();
                    location.reload();
                });
            });
        });

        setInterval(refreshTimerUi, 1000);
        refreshTimerUi();
    }

    /* --- Drag & drop (modo visual) --- */
    function initDnD() {
        if (modo !== 'visual' || !U.guardarRapido) return;
        var dragTareaId = null;
        var dragTareaNombre = '';
        document.querySelectorAll('.tarea-card[draggable="true"]').forEach(function (card) {
            card.addEventListener('dragstart', function (e) {
                dragTareaId = card.getAttribute('data-tarea-id');
                dragTareaNombre = card.getAttribute('data-tarea-nombre') || '';
                e.dataTransfer.setData('text/plain', dragTareaId);
                e.dataTransfer.effectAllowed = 'copy';
            });
        });

        var modal = document.getElementById('modal-drop-tiempo');
        var sub = document.getElementById('modal-drop-sub');
        var dropClienteId = null;

        document.querySelectorAll('.drop-zone').forEach(function (zone) {
            zone.addEventListener('dragover', function (e) {
                e.preventDefault();
                zone.classList.add('drag-over');
            });
            zone.addEventListener('dragleave', function () {
                zone.classList.remove('drag-over');
            });
            zone.addEventListener('drop', function (e) {
                e.preventDefault();
                zone.classList.remove('drag-over');
                dropClienteId = zone.getAttribute('data-drop-cliente');
                var card = zone.closest('.cliente-card-dnd');
                var nombreCliente = card ? card.querySelector('h3').textContent.replace(/^🏢\s*/, '') : '';
                if (sub) sub.textContent = nombreCliente + ' · ' + dragTareaNombre;
                if (modal) modal.style.display = 'flex';
            });
        });

        document.querySelectorAll('.btn-drop-min').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var min = parseInt(btn.getAttribute('data-min'), 10);
                if (!dropClienteId || !dragTareaId) return;
                postJson(U.guardarRapido, {
                    cliente_id: parseInt(dropClienteId, 10),
                    tarea_id: parseInt(dragTareaId, 10),
                    preset_minutos: min,
                }).then(function (res) {
                    if (!res.ok) {
                        alert(res.error || res.mensaje || 'Error');
                        return;
                    }
                    if (modal) modal.style.display = 'none';
                    notificarExterno('Horas registradas', res.mensaje || 'OK');
                    if (res.alerta_8h) notificarExterno('Aviso', 'Más de 8 h hoy.');
                });
            });
        });

        var cerr = document.getElementById('btn_cerrar_drop');
        if (cerr)
            cerr.addEventListener('click', function () {
                if (modal) modal.style.display = 'none';
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        pedirPermisoNotif();
        if (modo === 'quick') {
            initAutocomplete();
            initPlantillas();
            initTimer();
            actualizarStats();
            setInterval(actualizarStats, 60000);
            cargarHistorial();
            var br = document.getElementById('btn_refrescar_historial');
            if (br) br.addEventListener('click', cargarHistorial);
            var fp = document.getElementById('filtro-periodo');
            var fc = document.getElementById('filtro-cliente-hist');
            if (fp) fp.addEventListener('change', cargarHistorial);
            if (fc) fc.addEventListener('change', cargarHistorial);
        }
        initDnD();
    });
})();

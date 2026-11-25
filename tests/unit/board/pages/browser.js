// The page runs this after its vendored CSS, Turbo and Stimulus load.
const $ = selector => document.querySelector(selector)
const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
const key = (code, name = code, anchor = document.body, extra = {}) =>
  anchor.dispatchEvent(new KeyboardEvent('keydown', { code, key: name, bubbles: true, cancelable: true, ...extra }))
const ok = (test, message) => { if (!test) throw new Error(message) }
const pause = () => wait(100)
async function probe () {
  await pause()
  const which = document.documentElement.dataset.probe
  if (which === 'keys') {
    $('#side-fold').click()
    ok($('#shell').classList.contains('railed'), 'rail did not fold')
    ok($('#side-fold').title === 'Unfold the sidebar', 'rail action has the wrong label')
    const fold = $('#col-you button')
    fold.click()
    ok($('#col-you').classList.contains('folded'), 'column did not fold')
    fold.click()
    ok(!$('#col-you').classList.contains('folded'), 'column did not unfold')
    key('KeyJ', 'j')
    ok($('.tc[data-js-cur]'), 'J did not select a card')
    const before = $('.tc[data-js-cur]').closest('.col')
    key('KeyL', 'l')
    ok($('.tc[data-js-cur]').closest('.col') !== before, 'L did not select another column')
    key('KeyK', 'k', document.body, { metaKey: true })
    ok($('#search').hasAttribute('data-js-open'), 'Cmd-K did not open search')
    const search = $('[data-search-target=query]')
    search.value = 'Refund'
    search.dispatchEvent(new Event('input', { bubbles: true }))
    ok($('#sr-task-refund-rounding').hasAttribute('data-js-cur') ||
       $('#sr-task-refund-line-on-receipt').hasAttribute('data-js-cur'), 'search did not select a matching row')
    key('ArrowDown', 'ArrowDown', search)
    ok($('[data-search-target=row][data-js-cur]'), 'search did not move the selection')
    key('Escape', 'Escape', search)
    ok(!$('#search').hasAttribute('data-js-open'), 'Escape did not close search')
    $('[data-search-open]').click()
    let followed = false
    $('[data-search-target=row][data-js-cur]').addEventListener('click', event => {
      event.preventDefault()
      followed = true
    }, { once: true })
    key('Enter', 'Enter', search)
    ok(followed && !$('#search').hasAttribute('data-js-open'), 'search did not follow the marked result')
    key('KeyJ', 'j')
    const picked = $('.tc[data-js-cur] a.tc-link')
    let opened = false
    picked.addEventListener('click', event => { event.preventDefault(); opened = true }, { once: true })
    key('Enter', 'Enter')
    ok(opened, 'Enter did not open the marked task')
  } else if (which === 'panel') {
    $('.p-expand').click()
    ok($('#stage').classList.contains('full'), 'panel did not expand')
    $('.p-fold').click()
    ok($('.p-head').classList.contains('open'), 'details did not open')
    const grip = $('.p-grip')
    grip.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, button: 0, pointerId: 1 }))
    grip.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: 400, pointerId: 1 }))
    grip.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 }))
    ok($('#stage').style.getPropertyValue('--pw'), 'resize did not set a width')
    grip.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }))
    ok(!$('#stage').style.getPropertyValue('--pw'), 'reset kept the width')
    const tabs = $('.ptabs')
    const second = $('#ptab-criteria')
    let took = false
    tabs.addEventListener('click', event => { event.preventDefault(); took = event.target.closest('a') === second })
    key('Digit2', '2')
    ok(took, '2 did not select Criteria and decisions')
    $('.p-close').addEventListener('click', event => { event.preventDefault(); $('#panel').remove() })
    key('Escape', 'Escape')
    await pause()
    ok(!$('#panel') && document.activeElement.closest('#card-refund-line-on-receipt'), 'panel did not close or restore focus')
  } else if (which === 'backlog') {
    const query = $('#bl-query')
    key('Slash', '/')
    ok(document.activeElement === query, 'slash did not focus the filter')
    query.value = 'query'
    query.dispatchEvent(new Event('input', { bubbles: true }))
    ok($('[data-backlog-target=item][data-js-out]') && $('#item-export-in-one-query:not([data-js-out])'), 'text did not filter')
    query.focus()
    key('Enter', 'Enter', query)
    ok($('#item-export-in-one-query[data-js-cur]'), 'Enter did not mark the result')
    key('Enter', 'Enter')
    ok($('#item-export-in-one-query').open, 'Enter did not open the result')
    query.value = 'query'
    key('Escape', 'Escape', query)
    ok(query.value === '', 'Escape did not clear the filter')
    query.focus()
    key('Escape', 'Escape', query)
    ok(document.activeElement !== query, 'Escape did not leave the empty filter')
    const filter = search => {
      history.replaceState({}, '', search)
      document.dispatchEvent(new Event('turbo:morph'))
    }
    filter('?worth=yes')
    ok($('#item-invoice-footer-wraps:not([data-js-out])') && $('#item-export-in-one-query[data-js-out]'), 'worth did not filter')
    filter('?only=new')
    ok($('#item-invoice-footer-wraps:not([data-js-out])') && $('#item-export-in-one-query[data-js-out]'), 'new did not filter')
    filter('?only=stale')
    ok($('#item-export-in-one-query:not([data-js-out])') && $('#item-invoice-footer-wraps[data-js-out]'), 'stale did not filter')
    filter('?worth=unknown')
    ok(!$('.bl-item[data-js-out]'), 'an unknown filter hid an item')
    history.replaceState({}, '', '#item-export-in-one-query')
    window.dispatchEvent(new Event('hashchange'))
    ok($('#item-export-in-one-query[data-js-cur]').open, 'a named item did not open and take the mark')
    let copied = ''
    Object.defineProperty(navigator, 'clipboard', { configurable: true, get: () => ({ writeText: async words => { copied = words } }) })
    key('KeyS', 's')
    await pause()
    ok(copied.endsWith('docs/backlog/export-in-one-query.md'), 'S did not copy the marked command')
  } else if (which === 'waits') {
    key('KeyJ', 'j')
    const first = $('.wrow[data-js-cur]')
    ok(first, 'J did not mark a wait')
    key('ArrowDown', 'ArrowDown')
    ok($('.wrow[data-js-cur]') !== first, 'Down did not move the wait mark')
    let opened = false
    $('.wrow[data-js-cur] .wr-verb').addEventListener('click', event => { event.preventDefault(); opened = true })
    key('Enter', 'Enter')
    ok(opened, 'Enter did not open the marked wait')
    const stack = $('.wstack')
    const summary = stack.querySelector('summary')
    summary.click()
    ok(stack.open, 'click did not open the stack')
    summary.click()
    ok(!stack.open, 'click did not close the stack')
  } else if (which === 'chart') {
    for (let attempt = 0; !$('.chart[data-drawn=done]') && attempt < 30; attempt++) await pause()
    ok($('.chart[data-drawn=done] .pele'), $('.chart-err')?.textContent ?? 'Pele did not draw')
    const opener = $('.chart[data-drawn=done] .chart-open')
    opener.focus()
    opener.click()
    const dialog = $('#chart-large')
    const drawing = $('.cl-pane .pele')
    ok(dialog.open && drawing.style.getPropertyValue('--_fg'), 'large chart lost its palette')
    const percent = $('.cl-pct').textContent
    $('[data-zoom=in]').click()
    ok($('.cl-pct').textContent !== percent, 'zoom did not change')
    const stage = $('.cl-stage')
    const transform = $('.cl-pane').style.transform
    key('ArrowRight', 'ArrowRight', stage)
    ok($('.cl-pane').style.transform !== transform, 'pan did not change')
    key('Digit0', '0', stage)
    ok($('.cl-pct').textContent === percent, '0 did not fit')
    $('[data-zoom=close]').click()
    await pause()
    ok(!dialog.open && document.activeElement === opener, 'close did not return focus')
  } else if (which === 'merge') {
    const back = $('#confirm .cf-foot a')
    ok(back.getClientRects().length && getComputedStyle(back).visibility === 'visible', 'desktop merge cancel is hidden')
  } else if (which === 'copy') {
    const button = $('[title="Copy path"]')
    let copied = ''
    Object.defineProperty(navigator, 'clipboard', { configurable: true, get: () => ({ writeText: async words => { copied = words } }) })
    button.click()
    await pause()
    ok(copied === 'docs/backlog/file with spaces.md' && button.hasAttribute('data-js-done'), 'copy lost the path')
    button.removeAttribute('data-js-done')
    Object.defineProperty(navigator, 'clipboard', { configurable: true, get: () => ({ writeText: async () => { throw new Error('denied') } }) })
    document.execCommand = () => false
    button.click()
    await pause()
    ok(button.hasAttribute('data-js-copy-failed') && !button.hasAttribute('data-js-done'), 'a refusal showed success')
    const original = $('#arts')
    const next = original.cloneNode(true)
    $('#work-folder').open = false
    $('#ag-request > summary').click()
    await pause()
    original.replaceWith(next)
    await pause()
    ok(!$('#work-folder').open, 'artifact fold was lost across a tab visit')
    ok(!$('#ag-request').open, 'standard group fold was lost across a tab visit')
  } else if (which === 'drawer') {
    const tabs = [...document.querySelectorAll('.ktab')]
    const kanban = $('#kanban')
    const scroll = kanban.scrollTo.bind(kanban)
    let target
    kanban.scrollTo = options => { target = options.left; scroll({ ...options, behavior: 'instant' }) }
    tabs[2].click()
    ok(kanban.clientWidth > 0 && target === 2 * kanban.clientWidth, 'phone tab did not scroll to its column')
    kanban.dispatchEvent(new Event('scroll'))
    ok(tabs[2].dataset.jsOn === 'true', 'the selected phone tab did not change')
    $('[data-action="drawer#open"]').click()
    ok($('#shell').hasAttribute('data-js-drawer'), 'drawer did not open')
    key('Escape', 'Escape')
    ok(!$('#shell').hasAttribute('data-js-drawer'), 'drawer did not close')
    const menu = $('details[data-menu]')
    menu.open = true
    key('Escape', 'Escape')
    ok(!menu.open, 'menu did not close')
    menu.open = true
    document.body.click()
    ok(!menu.open, 'outside click did not close menu')
  }
}
window.addEventListener('load', () => {
  probe().then(() => { document.body.dataset.probeResult = 'passed' })
    .catch(error => { document.body.dataset.probeResult = error.message })
})

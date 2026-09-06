const $ = (selector) => document.querySelector(selector)
const pad = (value) => String(value).padStart(2, '0')
const asset = (path) => `.${path.startsWith('/') ? path : `/${path}`}`
const arrowIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

let allWorks = []
let allSeries = []
let selectedWork = null
let galleryIndex = 0
let previousFocus = null
let currentSeries = 'all'
let lastColumnCount = 0

const fetchJson = async (path) => {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`无法读取 ${path}`)
  return response.json()
}

const setText = (selector, value) => {
  const element = $(selector)
  if (element) element.textContent = value ?? ''
}

const renderSite = (site) => {
  document.title = `${site.studioName}｜个人艺术作品集`
  setText('#brand-mark', site.artistName.slice(0, 1).toUpperCase())
  setText('#brand-name', site.studioName)
  setText('#availability-text', site.availability)
  setText('#hero-eyebrow', `${site.role} · ${site.location}`)
  setText('#hero-title', site.heroTitle)
  setText('#hero-accent', site.heroAccent)
  setText('#hero-intro', site.heroIntro)
  $('#hero-image').src = asset(site.heroImage)
  $('#hero-image').alt = site.heroImageAlt
  setText('#portrait-caption', `${site.location}，2026`)
  $('#portrait-image').src = asset(site.portrait)
  $('#portrait-image').alt = site.portraitAlt
  setText('#about-title-text', site.aboutTitle)
  setText('#about-accent', site.aboutAccent)
  $('#about-body').innerHTML = (site.aboutParagraphs || []).map((paragraph) => `<p>${paragraph}</p>`).join('')
  setText('#contact-intro', site.contactIntro)
  setText('#copyright', `© 2026 ${site.studioName}. All works reserved.`)
  $('#contact-methods').innerHTML = `
    <a href="mailto:${site.email}"><span>邮箱</span><strong>${site.email}</strong>${arrowIcon}</a>
    <div><span>微信</span><strong>${site.wechat}</strong></div>
    <a href="${site.socialUrl}" target="_blank" rel="noreferrer"><span>社交媒体</span><strong>${site.socialLabel}</strong>${arrowIcon}</a>`
}

const renderMarquee = () => {
  const content = allSeries.map((item) => `<span>${item.title}<i></i></span>`).join('')
  $('#marquee-track').innerHTML = `<div class="marquee-content">${content}</div><div class="marquee-content">${content}</div>`
}

const renderSeries = () => {
  $('#series-list').innerHTML = allSeries.map((item, index) => {
    const count = allWorks.filter((work) => work.series === item.slug).length
    return `
    <button class="series-row" type="button" data-series="${item.slug}">
      <span>${pad(index + 1)}</span>
      <span class="series-name"><strong>${item.title}</strong><small>${item.titleEn || ''}</small></span>
      <span class="series-period">${count} 件作品</span>
      <span class="series-arrow">${arrowIcon}</span>
    </button>`
  }).join('')

  const linkedSeries = allSeries.filter((item) => item.linkUrl)
  $('#series-links').innerHTML = linkedSeries.map((item) => `
    <a href="${item.linkUrl}" target="_blank" rel="noreferrer">
      <span>${item.title}</span><strong>${item.linkLabel || '查看相关项目'}</strong>${arrowIcon}
    </a>`).join('')
  $('#series-links').hidden = linkedSeries.length === 0

  $('#series-list').addEventListener('click', (event) => {
    const row = event.target.closest('[data-series]')
    if (!row) return
    selectSeries(row.dataset.series)
    $('#works').scrollIntoView({ behavior: 'smooth' })
  })
}

const renderFilters = (active = 'all') => {
  $('#filters').innerHTML = `<button type="button" data-filter="all" class="${active === 'all' ? 'active' : ''}">全部</button>${allSeries.map((item) => `<button type="button" data-filter="${item.slug}" class="${active === item.slug ? 'active' : ''}">${item.title}</button>`).join('')}`
}

const workCardHtml = (work, index) => {
  const ratio = work.width && work.height ? ` style="aspect-ratio:${work.width} / ${work.height}"` : ''
  return `
  <article class="work-card ${work.layout || 'natural'}">
    <button class="work-open" type="button" data-work="${work.slug}" aria-label="查看作品《${work.title}》">
      <span class="art-frame"${ratio}><img src="${asset(work.image)}" alt="${work.alt}" width="${work.width || 'auto'}" height="${work.height || 'auto'}" loading="${index > 1 ? 'lazy' : 'eager'}" decoding="async"><span class="view-work">查看作品</span></span>
      <span class="work-info"><span><strong>${work.title}</strong><small>${work.medium} · ${work.year}</small></span><span class="work-number">${pad(work.order)}</span></span>
    </button>
  </article>`
}

const galleryColumnCount = () => {
  if (window.matchMedia('(max-width: 700px)').matches) return 1
  if (window.matchMedia('(max-width: 1080px)').matches) return 2
  return 3
}

const CAPTION_UNITS = 0.09
const estimatedCardHeight = (work) => (work.width && work.height ? work.height / work.width : 0.8) + CAPTION_UNITS

const distributeIntoColumns = (works, count) => {
  const columns = Array.from({ length: count }, () => ({ items: [], height: 0 }))
  works.forEach((work) => {
    const target = columns.reduce((shortest, column) => (column.height < shortest.height ? column : shortest), columns[0])
    target.items.push(work)
    target.height += estimatedCardHeight(work)
  })
  return columns.map((column) => column.items)
}

const renderWorks = (active = 'all') => {
  const visible = active === 'all' ? allWorks : allWorks.filter((work) => work.series === active)
  const count = Math.min(galleryColumnCount(), Math.max(visible.length, 1))
  $('#works-grid').innerHTML = distributeIntoColumns(visible, count)
    .map((column) => `<div class="works-col">${column.map((work) => workCardHtml(work, allWorks.indexOf(work))).join('')}</div>`)
    .join('') || '<p class="empty-state">这个系列的作品正在整理中。</p>'
}

const selectSeries = (slug) => {
  currentSeries = slug
  renderFilters(slug)
  renderWorks(slug)
}

const updateLightboxImage = () => {
  const gallery = [selectedWork.image, ...(selectedWork.gallery || [])]
  $('#lightbox-image').src = asset(gallery[galleryIndex])
  $('#lightbox-image').alt = selectedWork.alt
  $('#gallery-count').textContent = `${galleryIndex + 1} / ${gallery.length}`
  $('#gallery-controls').hidden = gallery.length < 2
}

const openWork = (work) => {
  previousFocus = document.activeElement
  selectedWork = work
  galleryIndex = 0
  const series = allSeries.find((item) => item.slug === work.series)
  setText('#lightbox-index', `${pad(work.order)} / ${pad(allWorks.length)}`)
  setText('#lightbox-series', `${series?.title || ''} · ${series?.titleEn || ''}`)
  setText('#lightbox-title', work.title)
  setText('#lightbox-title-en', work.titleEn || '')
  setText('#lightbox-description', work.description)
  $('#lightbox-meta').innerHTML = `<div><dt>年份</dt><dd>${work.year}</dd></div><div><dt>媒介</dt><dd>${work.medium}</dd></div>${work.dimensions ? `<div><dt>尺寸</dt><dd>${work.dimensions}</dd></div>` : ''}`
  updateLightboxImage()
  $('#lightbox').hidden = false
  document.body.classList.add('locked')
  requestAnimationFrame(() => $('#close-lightbox').focus())
}

const closeLightbox = () => {
  $('#lightbox').hidden = true
  document.body.classList.remove('locked')
  selectedWork = null
  previousFocus?.focus()
}

const bindInteractions = () => {
  const menuButton = $('#menu-button')
  const menu = $('#nav-links')
  const closeMenu = () => {
    menu.classList.remove('is-open')
    menuButton.setAttribute('aria-expanded', 'false')
    menuButton.setAttribute('aria-label', '打开菜单')
    document.body.classList.remove('locked')
  }
  menuButton.addEventListener('click', () => {
    const open = !menu.classList.contains('is-open')
    menu.classList.toggle('is-open', open)
    menuButton.setAttribute('aria-expanded', String(open))
    menuButton.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单')
    document.body.classList.toggle('locked', open)
  })
  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu()
  })
  $('#filters').addEventListener('click', (event) => {
    const button = event.target.closest('[data-filter]')
    if (button) selectSeries(button.dataset.filter)
  })
  $('#works-grid').addEventListener('click', (event) => {
    const button = event.target.closest('[data-work]')
    const work = button ? allWorks.find((item) => item.slug === button.dataset.work) : null
    if (work) openWork(work)
  })
  $('#close-lightbox').addEventListener('click', closeLightbox)
  $('#lightbox').addEventListener('mousedown', (event) => {
    if (event.target === event.currentTarget) closeLightbox()
  })
  $('#previous-image').addEventListener('click', () => {
    const length = 1 + (selectedWork.gallery || []).length
    galleryIndex = (galleryIndex - 1 + length) % length
    updateLightboxImage()
  })
  $('#next-image').addEventListener('click', () => {
    const length = 1 + (selectedWork.gallery || []).length
    galleryIndex = (galleryIndex + 1) % length
    updateLightboxImage()
  })
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      if (!$('#lightbox').hidden) closeLightbox()
      closeMenu()
    }
  })
}

const start = async () => {
  try {
    const [site, series, works] = await Promise.all([
      fetchJson('./content/site.json'),
      fetchJson('./content/series.json'),
      fetchJson('./content/works.json'),
    ])
    allSeries = series.filter((item) => item.published).sort((a, b) => a.order - b.order)
    allWorks = works.filter((item) => item.published).sort((a, b) => a.order - b.order)
    renderSite(site)
    renderMarquee()
    renderSeries()
    renderFilters()
    renderWorks()
    bindInteractions()
    lastColumnCount = galleryColumnCount()
    window.addEventListener('resize', () => {
      const count = galleryColumnCount()
      if (count !== lastColumnCount) {
        lastColumnCount = count
        renderWorks(currentSeries)
      }
    })
  } catch (error) {
    console.error(error)
    $('#works-grid').innerHTML = '<p class="empty-state">作品内容暂时无法读取，请通过本地服务器或 GitHub Pages 打开网站。</p>'
  }
}

start()

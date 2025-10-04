// --- Create a <x-dso> tag that generates SIMBAD previews for DSOs on hover ---
document.addEventListener('DOMContentLoaded', (e) => {
class XDsoElement extends HTMLElement {
    // Ref: https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_custom_elements and https://mdn.github.io/web-components-examples/popup-info-box-web-component/
    constructor() {
	super();
    }

    connectedCallback() {
	if (document.disableDSO) {
	    return;
	}
	const shadow = this.attachShadow({ mode: "open" });

	const wrapper = document.createElement("span");
	wrapper.setAttribute("class", "x-dso-wrapper");

	const span = document.createElement("span");
	span.setAttribute("class", "x-dso-span");
//	setTimeout(() => { // https://stackoverflow.com/questions/62962138/how-to-get-the-contents-of-a-custom-element
	    span.innerHTML = this.innerHTML;
//	});
	const info = document.createElement("div");
	info.setAttribute("class", "x-dso-info");
	const iframe = document.createElement("iframe");
	info.appendChild(iframe);
	span.addEventListener("mouseover", () => {
	    // let full_url = 'https://simbad.u-strasbg.fr/simbad/sim-id?Ident=' + encodeURIComponent(this.hasAttribute("simbad") ? this.getAttribute("simbad") : this.innerHTML);
	    let preview_url = 'https://simbad.u-strasbg.fr/mobile/object.html?object_name=' + encodeURIComponent(this.hasAttribute("simbad") ? this.getAttribute("simbad") : this.innerHTML);
	    if (!!!iframe.src) {
		iframe.src = preview_url;
	    }
	});

	const stylesheet = document.createElement("link");
	stylesheet.setAttribute('rel', 'stylesheet');
	stylesheet.setAttribute('href', '/assets/x-dso.css');

	shadow.appendChild(stylesheet);
	shadow.appendChild(wrapper);
	wrapper.appendChild(span);
	wrapper.appendChild(info);

    }
}

customElements.define("x-dso", XDsoElement);

// --- Create a <x-dso-link> tag that adds SIMBAD links to DSOs ---
class XDsoLinkElement extends HTMLElement {
    constructor() {
	super();
    }

    connectedCallback() {
	const shadow = this.attachShadow({ mode: "open" });
	const anchor = document.createElement("a");
	anchor.setAttribute("target", "_blank");
	anchor.style = "color: var(--link-color); text-underline-offset: 2px;";
//	setTimeout(() => { // https://stackoverflow.com/questions/62962138/how-to-get-the-contents-of-a-custom-element
	    anchor.setAttribute("href", 'https://simbad.u-strasbg.fr/simbad/sim-id?Ident=' + encodeURIComponent(this.hasAttribute("simbad") ? this.getAttribute("simbad") : this.innerHTML.trim()));
	    anchor.innerHTML = this.innerHTML.trim();
//	});
	shadow.appendChild(anchor);
    }

}
customElements.define("x-dso-link", XDsoLinkElement);
}); // DOM Load callback

// ------

// CSV Maker
{
    let script = document.createElement('script');
    script.src = 'assets/csv_maker.js';
    document.head.appendChild(script);
}
// Font Awesome v4.7.0
{
    let link = document.createElement('link');
    link.href = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
    link.rel = 'stylesheet'
    document.head.appendChild(link);
}
// Favicon
{
    let favicon = document.createElement('link');
    favicon.rel = 'shortcut icon';
    favicon.href = 'assets/favicon.ico';
    document.head.appendChild(favicon);
}

// Navigation and Header Bar
{
    // Taken from https://stackoverflow.com/questions/31954089/how-can-i-reuse-a-navigation-bar-on-multiple-pages
    let headbar = document.createElement('div');
    headbar.id = 'headbar';
    headbar.setAttribute('class', 'headbar');

    // Overflow detection for navigation and header bar (ChatGPT)
    function updateNavbarOverflow() {
	console.log("in updateNavbarOverflow()");
	const itemsContainer = headbar.querySelector('.headbar-contents');
	const overflowContainer = document.getElementById('headbar-overflow');
	const kebab = headbar.querySelector('.headbar-kebab-btn');
	const darkModeButton = headbar.querySelector('.darkmode-button')

	// Reset dropdown
	overflowContainer.innerHTML = '';
	kebab.style.display = 'none';

	const gap = 8;
	const navWidth = itemsContainer.offsetWidth;

	const items = Array.from(itemsContainer.children);

	let nonFoldableWidth = gap;
	items.forEach(item => {
	    item.style.display = 'inline-flex';
	    if (!item.classList.contains('headbar-foldable'))
		nonFoldableWidth += item.offsetWidth + gap;
	});
	let totalWidth = nonFoldableWidth;

	let overflowCount = 0;
	items.forEach(item => {
	    if (!item.classList.contains('headbar-foldable'))
		return;
	    totalWidth += item.offsetWidth + gap; // include gap
	    if (item.classList.contains('headbar-overflow'))
		return;
	    if (totalWidth > headbar.offsetWidth) {
		// Move overflow items into dropdown
		overflow_item = item.cloneNode(true);
		overflow_item.style.display = 'block';
		overflowContainer.appendChild(overflow_item);
		++overflowCount;
		item.style.display = 'none';
	    }
	});
	if (overflowCount > 0) {
	    kebab.style.display = 'inline-flex';
	} else {
	    kebab.style.display = 'none';
	}
    }

    let promise = fetch('headbar.html').then(res => res.text()).then(
	text => {
	    headbar.innerHTML = text;
	});
	    
    window.addEventListener('load', () => {
	var body = document.body;
	body.insertBefore(headbar, body.firstChild);

	function _update_navbar() {
	    let overflow = document.getElementById('headbar-overflow');
	    let kebab = document.getElementById('headbar-kebab-btn');
	    if (kebab && overflow) {
		kebab.addEventListener('click', () => {
		    overflow.classList.toggle('show');
		});
		updateNavbarOverflow();
	    } else {
		setTimeout(_update_navbar, 100);
	    }
	}
	_update_navbar();
    });
    
    window.addEventListener('resize', updateNavbarOverflow);

}
    
// Following is based on https://stackoverflow.com/questions/56300132/how-to-override-css-prefers-color-scheme-setting
// Determine if the user has a set theme
function detectColorScheme(){
    var theme="light";    //default to light

    //local storage is used to override OS theme settings
    if(localStorage.getItem("theme")){
        if(localStorage.getItem("theme") == "dark"){
            var theme = "dark";
        }
    } else if(!window.matchMedia) {
        //matchMedia method not supported
        return false;
    } else if(window.matchMedia("(prefers-color-scheme: dark)").matches) {
        //OS theme setting detected as dark
        var theme = "dark";
    }

    //dark theme preferred, set document with a `data-theme` attribute
    if (theme == "dark") {
         document.documentElement.setAttribute("data-theme", "dark");
    }
}
detectColorScheme();

function toggleDarkMode() {
    if (document.documentElement.getAttribute("data-theme") != "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
	localStorage.setItem("theme", "dark");
    } else {
        document.documentElement.setAttribute("data-theme", "light");
	localStorage.setItem("theme", "light");
    }
}

function raDegreesToHMS(degrees) {
  const totalHours = degrees / 15;
  const hours = Math.floor(totalHours);
  const minutesFloat = (totalHours - hours) * 60;
  const minutes = Math.floor(minutesFloat);
  const seconds = ((minutesFloat - minutes) * 60).toFixed(2);

  const padZero = val => String(val).padStart(2, '0');

  return `${padZero(hours)}h ${padZero(minutes)}m ${padZero(seconds)}s`;
}

function decDegreesToDMS(degrees) {
  const sign = degrees < 0 ? '-' : '+';
  const absDegrees = Math.abs(degrees);
  const d = Math.floor(absDegrees);
  const minutesFloat = (absDegrees - d) * 60;
  const m = Math.floor(minutesFloat);
  const s = ((minutesFloat - m) * 60).toFixed(2);

  const padZero = val => String(val).padStart(2, '0');

  return `${sign}${padZero(d)}° ${padZero(m)}' ${padZero(s)}"`;
}

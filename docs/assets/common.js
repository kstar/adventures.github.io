// --- Create a <x-dso> tag that generates SIMBAD previews for DSOs on hover ---
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
	setTimeout(() => { // https://stackoverflow.com/questions/62962138/how-to-get-the-contents-of-a-custom-element
	    span.innerHTML = this.innerHTML;
	});
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

	const style = document.createElement("style");

	style.textContent = `
      .x-dso-wrapper {
        position: relative;
      }

      .x-dso-info {
        font-size: 0.8rem;
        width: 400px;
        height: 400px;
        border: 1px solid black;
        padding: 5px;
        background: white;
        border-radius: 10px;
        display: none;
        transition: 0.6s all;
        position: absolute;
        bottom: 10px;
        left: 0px;
        z-index: 3;
      }

      .x-dso-info iframe {
        width: 800px;
        height: 800px;
        display: block;
        -ms-zoom: 0.5;
        -moz-transform: scale(0.5);
        -moz-transform-origin: 0 0;
        -o-transform: scale(0.5);
        -o-transform-origin: 0 0;
        -webkit-transform: scale(0.5);
        -webkit-transform-origin: 0 0;
      }

      .x-dso-span {
        text-decoration:underline;
        text-decoration-style: dotted;
      }

      .x-dso-span:hover + .x-dso-info, .x-dso-span:focus + .x-dso-info {
        display: block;
      }
      .x-dso-info:hover {
        display: block;
      }
    `;

    shadow.appendChild(style);
    shadow.appendChild(wrapper);
    wrapper.appendChild(span);
    wrapper.appendChild(info);

    }
}

customElements.define("x-dso", XDsoElement);

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

    fetch('headbar.html').then(res => res.text()).then(
	text => {
	    headbar.innerHTML = text;
	});
    window.onload = () => {
	var body = document.body;
	body.insertBefore(headbar, body.firstChild);
    }
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

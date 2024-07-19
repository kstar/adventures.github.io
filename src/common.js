// --- Create a <x-dso> tag that generates SIMBAD previews for DSOs on hover ---
class XDsoElement extends HTMLElement {
    // Ref: https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_custom_elements and https://mdn.github.io/web-components-examples/popup-info-box-web-component/
    constructor() {
	super();
    }

    connectedCallback() {
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
	console.log(style.isConnected); // ?

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
        bottom: 20px;
        left: 10px;
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
    console.log(style.isConnected); // ?
    shadow.appendChild(wrapper);
    wrapper.appendChild(span);
    wrapper.appendChild(info);

    }
}

customElements.define("x-dso", XDsoElement);
// ------


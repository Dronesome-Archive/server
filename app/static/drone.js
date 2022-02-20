// style
const colors = {
	line: '#008800',
	lineActive: '#00FF00',
	drone: '#FFFFFF',
	facility: '#008800',
	facilityGoal: '#00FF00',
	facilityHome: '#000088',
	facilityHomeGoal: '#0000FF',
}

// DOM
let droneButtons = {};
let batteryDisplay;
let stateDisplay;
let stateContainer;

// API
let accessToken = '';
let canControl = false;

// facility data (set at the beginning)
let facilities = [];
let ownFacility = null;
let homeFacility = null;

// facility data (set dynamically)
let goalFacility = null;
let facilityState = '';
let droneRequested = false;

// map icons
let map = null;
let droneMarker = null;
let facilityMarkers = [];
let facilityLines = [];
let currentFacilityLine = null;


function init() {
	// get DOM elements
	batteryDisplay = document.getElementById('battery_display');
	stateDisplay = document.getElementById('state_display');
	stateContainer = document.getElementById('state_container');

	// create drone buttons
	for (const button of ['request', 'allowTakeoff', 'emergencyReturn', 'emergencyLand', 'crashed']) {
		droneButtons[button] = createButton(document.getElementById('drone_buttons'));
	}
	droneButtons.request.show = showRequest;
	droneButtons.allowTakeoff.show = showAllowTakeoff;
	droneButtons.emergencyReturn.show = showEmergencyReturn;
	droneButtons.emergencyLand.show = showEmergencyLand;
	droneButtons.crashed.show = showCrashed;

	// init map
	map = L.map('map').setView(ownFacility.pos, 13);
	L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		maxZoom: 18,
		id: 'mapbox/streets-v11',
		tileSize: 512,
		zoomOffset: -1,
		accessToken: accessToken
	}).addTo(map);
	
	// drone marker
	droneMarker = L.marker([0.0, 0.0], {title: 'Kurier', color: colors.drone});

	// map items
	for (const facilityId in facilities) {
		// facility marker
		facilityMarkers[facilityId] = L.marker(
			facilities[facilityId].pos,
			{
				title: facilities[facilityId].name,
				color: (facilities[facilityId] == homeFacility) ? colors.facilityHome : colors.facility,
			}
		).addTo(map);
		// facility line
		if (facilities[facilityId] !== homeFacility) {
			facilityLines[facilityId] = L.polyline(
				[facilities[facilityId].pos].concat(facilities[facilityId].waypoints).concat([homeFacility.pos]),
				{color: colors.line}
			).addTo(map);
		}
	}

	// connect via socketio
	const socket = io('/frontend');
	socket.on('facility_state', onFacilityState);
	socket.on('drone_state', onDroneState);
	socket.on('heartbeat', onHeartbeat);
	socket.on('drone_requested', onDroneRequested);
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// BUTTONS
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function createButton(parent) {
	let button = {
		dom: document.createElement('button'),
		show: null,
		hide: function() {
			this.dom.className = 'item';
			this.dom.style.display = 'none';
			this.dom.onclick = null;
			this.dom.innerText = '';
		}
	}
	parent.appendChild(button.dom);
	button.hide();
	return button;
}

showRequest = function(requested) {
	this.dom.style.display = 'initial';
	if (requested) {
		this.dom.innerText = "Kurier angefordert";
	} else {
		this.dom.innerText = "Kurier anfordern";
		this.dom.classList.add('good_step');
		this.dom.onclick = () => window.location.href = '/drone_control/request';
	}
}

showAllowTakeoff = function() {
	this.dom.style.display = 'initial';
	this.dom.innerText = "Starterlaubnis erteilen";
	this.dom.classList.add('good_step');
	this.dom.onclick = () => window.location.href = '/drone_control/allow_takeoff'
}

showEmergencyReturn = function() {
	this.dom.style.display = 'initial';
	this.dom.innerText = "Sofort umkehren";
	this.dom.classList.add('bad_step');
	this.dom.onclick = () => showPopup('emergency_return');
}

showEmergencyLand = function() {
	this.dom.style.display = 'initial';
	this.dom.innerText = "Sofort notlanden";
	this.dom.classList.add('bad_step');
	this.dom.onclick = () => showPopup('emergency_land');
}

showCrashed = function(show) {
	this.dom.style.display = 'initial';
	this.dom.innerText = "Notgelandet";
	this.dom.classList.add('bad_step');
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// SOCKETIO EVENT HANDLERS
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function onFacilityState(args) {
	console.log('onFacilityState', args);
	goalFacility = facilities[args.goal_id];

	// facility marker colors
	for (const facilityId in facilities) {
		if (facilityId == homeFacility.id == goalFacility.id)
			facilityMarkers[facilityId].color = colors.facilityHomeGoal;
		else if (facilityId == homeFacility.id)
			facilityMarkers[facilityId].color = colors.facilityHome;
		else if (facilityId == goalFacility.id)
			facilityMarkers[facilityId].color = colors.facilityGoal;
		else
			facilityMarkers[facilityId].color = colors.facility;
	}

	// facility line colors
	if (goalFacility == homeFacility && args.state === 'idle') {
		for (const facilityLineId in facilityLines) {
			facilityLines[facilityLineId].color = colors.line;
		}
	} else if (goalFacility != homeFacility) {
		facilityLines[goalFacility.id].color = colors.lineActive;
	}

	// drone state
	if (args.state === 'idle' && goalFacility != ownFacility) {
		stateContainer.style.display = 'none';
		droneMarker.remove();
	} else {
		stateContainer.style.display = 'initial';
		droneMarker.addTo(map);
	}

	// request button
	if (ownFacility != goalFacility && ownFacility != homeFacility) droneButtons.request.show(droneRequested);
	else droneButtons.request.hide();

	// allowTakeoff button
	if (args.state == 'awaiting_takeoff' && goalFacility != ownFacility) droneButtons.allowTakeoff.show();
	else droneButtons.allowTakeoff.hide();

	// emergencyReturn button
	if (args.state == 'en_route') droneButtons.emergencyReturn.show();
	else droneButtons.emergencyReturn.hide();

	// emergencyLand button
	if (args.state == 'en_route' || args.state == 'returning') droneButtons.emergencyLand.show();
	else droneButtons.emergencyLand.hide();

	// crashed button
	if (args.state == 'emergency') droneButtons.crashed.show();
	else droneButtons.crashed.hide();
}

function onHeartbeat(args) {
	console.log('onHeartbeat', args);
	batteryDisplay.children[0].style.width = (args.battery*100)+'%';
	droneMarker.setLatLng(args.pos);
}

function onDroneState(args) {
	console.log('onDroneState', args);
	let states = {
		'idle': "Am Boden",
		'en_route': "Fliegt",
		'landing': "Landet",
		'return_landing': "Landet",
		'returning': "Kehrt zurück",
		'emergency_landing': "Macht Notlandung",
		'crashed': "Notgelandet",
		'updating': "Empfängt Mission"
	};
	stateDisplay.innerText = states[args.state];
}

function onDroneRequested(args) {
	console.log('onDroneRequested', args);
	droneRequested = args.requested; // only true when we are waiting for the mission to start
	if (ownFacility != goalFacility && ownFacility != homeFacility) droneButtons.request.show(droneRequested);
}

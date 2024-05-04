function showMatchAndSplit() {
	if ( mw.config.get('wgWikiFamily') !== 'wikisource' ) {
		return;
	}

    const url = new URL(window.location.href);

    let lang = url.hostname.split('.')[0];

    if ( url.hostname.startsWith( 'wikisource' ) ) {
		lang = 'old';
	}

    if ( mw.config.get('wgNamespaceNumber') !== 0 ) {
        return;
    }

    const matchPortlet = mw.util.addPortletLink(
		'p-cactions',
        '#',
		'Run match on page [EXPERIMENTAL] ',
		'ca-match',
	);

    matchPortlet.addEventListener('click', async function() {
        await fetch('https://matchandsplit.toolforge.org/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lang: lang,
                title: mw.config.get('wgPageName'),
                username: mw.config.get( 'wgUserName' ),
            }),
        });
    });

    const splitPortlet = mw.util.addPortletLink(
		'p-cactions',
        '#',
		'Run split on page [EXPERIMENTAL]',
		'ca-split',
	);

    splitPortlet.addEventListener('click', async function() {
        await fetch('https://matchandsplit.toolforge.org/split', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lang: lang,
                title: mw.config.get('wgPageName'),
                username: mw.config.get( 'wgUserName' ),
            }),
        });
    });
}

window.addEventListener( 'load', function() {
    mw.loader.using( 'mediawiki.util', showMatchAndSplit );
} );
# Historical preflight artifact notice

The adjacent wack_preflight_20261001.xml and .json files were created by the old --preflight implementation. That code generated six PASS values without building a package or invoking the Windows App Certification Kit.

The values are retained as historical synthetic data, not WACK results. The XML now carries an explicit SYNTHETIC NOT WACK comment; the JSON carries artifact_classification: SYNTHETIC_NOT_WACK and wack_executed: false. The current report parser rejects the historical filename and the explicit XML marker.

Do not cite these files as package, runtime, signature, Windows App Certification Kit, Store submission, or Store approval evidence.

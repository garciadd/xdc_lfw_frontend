function (id, type, meta, ctx) {
    if (type === "custom_metadata" && meta['onedata_json'] && meta['onedata_json']['eml:eml'] && meta['onedata_json']['eml:eml']['dataset'] && meta['onedata_json']['eml:eml']['dataset']['title']){
        return [
            [
                meta['onedata_json']['eml:eml']['dataset']['title']
            ],
            id
        ];
    }
    return null;
}
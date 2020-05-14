function (id, type, meta, ctx) {
    if (type === "custom_metadata" && meta['onedata_json'] && meta['onedata_json']['eml:eml'] && meta['onedata_json']['eml:eml']['dataset'] && meta['onedata_json']['eml:eml']['dataset']['coverage'] && meta['onedata_json']['eml:eml']['dataset']['title'] && meta['onedata_json']['eml:eml']['dataset']['title'].includes("LC8") && meta['onedata_json']['eml:eml']['dataset']['coverage'] && meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage'] && meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates'] && meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates'] && meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates']['beginDate'] && meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates']['beginDate']['calendarDate']){
        
        return [
            Number(new Date(meta['onedata_json']['eml:eml']['dataset']['coverage']['temporalCoverage']['rangeOfDates']['beginDate']['calendarDate'])),
            meta['onedata_json']['eml:eml']['dataset']['title'],
            id
        ];
    }
    return null;
}
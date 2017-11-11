# pyasterix

EUROCONTROL ASTERIX encoder/decoder

A library that encodes and decodes in the EUROCONTROL ASTERIX format as
specified in the document EUROCONTROL-SPEC-0149.

refrence from: https://github.com/vitorafsr/asterixed

sample code:

    def bytes2hexstr(_bytes):
        return "".join("%02X" % b for b in _bytes)

    hexstr = '15004EFF9FB35B83E40001080001014CFBA315CD2A4A0EAF0AE69555250757D74CFB330005554CFBA31189374B4CFB3319CAC08341C60A00500C000000F500004CFBB3414175D75820006A06D901'
    ad = AsterixDecoder(bytearray.fromhex(hexstr))
    print(ad.get_result())

    ae = AsterixEncoder({'21':ad.get_result()})
    hexstr2 = bytes2hexstr(ae.get_result())
    print(hexstr2)
    assert(hexstr == hexstr2)

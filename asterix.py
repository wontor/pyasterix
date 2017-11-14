'''
EUROCONTROL ASTERIX encoder/decoder

A library that encodes and decodes in the EUROCONTROL ASTERIX format as
specified in the document EUROCONTROL-SPEC-0149.
Edition Number: 0.99
Edition Date: 2017.11.11

Category specifications Xml files in the "config/" directory were taken from
https://github.com/CroatiaControlLtd/asterix/tree/master/install/config
These files were public under GPLv3 license.
'''

__copyright__ = '''\
The MIT License (MIT)

Copyright (c) 2017 asterix.py wontor@126.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
from xml.dom import minidom


filenames = {
    1: 'config/asterix_cat001_1_1.xml',
    2: 'config/asterix_cat002_1_0.xml',
    8: 'config/asterix_cat008_1_0.xml',
    10: 'config/asterix_cat010_1_1.xml',
    19: 'config/asterix_cat019_1_2.xml',
    20: 'config/asterix_cat020_1_7.xml',
    # 21:'config/asterix_cat021_0_26.xml',
    21: 'config/asterix_cat021_1_8.xml',
    23: 'config/asterix_cat023_1_2.xml',
    30: 'config/asterix_cat030_6_2.xml',
    31: 'config/asterix_cat031_6_2.xml',
    # 32:'config/asterix_cat032_6_2.xml',
    32: 'config/asterix_cat032_7_0.xml',
    48: 'config/asterix_cat048_1_14.xml',
    # 62:'config/asterix_cat062_0_17.xml',
    # 62:'config/asterix_cat062_1_9.xml',
    62: 'config/asterix_cat062_1_16.xml',
    # 62:'config/asterix_cat062_1_7.xml',
    63: 'config/asterix_cat063_1_3.xml',
    65: 'config/asterix_cat065_1_3.xml',
    # 65:'config/asterix_cat065_1_2.xml',
    242: 'config/asterix_cat242_1_0.xml',
    # 252:'config/asterix_cat252_6_2.xml',
    252: 'config/asterix_cat252_7_0.xml',
    # 252:'config/asterix_cat252_6_1.xml'}
}


class AsterixEncoder():
    def __init__(self, asterix):
        assert type(asterix) is dict
        self.asterixs = asterix

        asterixkey = list(self.asterixs.keys())[0]
        cat = int(asterixkey)  # assert

        try:
            self.cat = minidom.parse(filenames[cat])
            category = self.cat.getElementsByTagName('Category')[0]
            self.dataitems = category.getElementsByTagName('DataItem')
            uap = category.getElementsByTagName('UAP')[0]
            self.uapitems = uap.getElementsByTagName('UAPItem')
        except:
            print('wrong input data format or %d not supported now' % cat)
            return

        self.encorded_result = bytearray()
        self.encorded_result += bytes([cat])
        self.encorded_result += bytes([0, 0])

        self.asterixs = self.asterixs[asterixkey]
        if type(self.asterixs) is dict:
            self.asterixs = [self.asterixs]

        for asterix in self.asterixs:
            self.encoded = bytearray()
            self.asterix = asterix
            self.encode()

            self.encorded_result += self.encoded

        length = len(self.encorded_result)
        self.encorded_result[1:3] = (length).to_bytes(2, 'big')

    def get_result(self):
        return self.encorded_result

    def encode(self):
        # encoded length, tmp to 0

        FSPEC_bits = 0
        FSPEC_bits_len = 0

        for uapitem in reversed(self.uapitems):
            # FX field
            if FSPEC_bits_len % 8 == 0:
                if FSPEC_bits != 0:
                    FSPEC_bits += (1 << FSPEC_bits_len)
                else:  # if all the previous field is zero, discard it
                    FSPEC_bits_len = 0
                FSPEC_bits_len += 1
                continue

            # other uapitem field
            id = uapitem.firstChild.nodeValue
            if id in self.asterix:
                if not self.asterix[id]:   # if self.asterix[id] is blank, delete it
                    del self.asterix[id]
                    continue
                FSPEC_bits += (1 << FSPEC_bits_len)

            FSPEC_bits_len += 1

        self.encoded += (FSPEC_bits).to_bytes(FSPEC_bits_len //
                                              8, byteorder='big')

        for uapitem in self.uapitems:
            id = uapitem.firstChild.nodeValue
            if id not in self.asterix:
                continue

            for dataitem in self.dataitems:
                itemid = dataitem.getAttribute('id')
                if itemid == id:
                    dataitemformat = dataitem.getElementsByTagName('DataItemFormat')[
                        0]
                    for cn in dataitemformat.childNodes:
                        r = None
                        if cn.nodeName == 'Fixed':
                            n, r = self.encode_fixed(self.asterix[itemid], cn)
                        elif cn.nodeName == 'Repetitive':
                            n, r = self.encode_repetitive(
                                self.asterix[itemid], cn)
                        elif cn.nodeName == 'Variable':
                            n, r = self.encode_variable(
                                self.asterix[itemid], cn)
                        elif cn.nodeName == 'Compound':
                            n, r = self.encode_compound(
                                self.asterix[itemid], cn)

                        if r:
                            self.encoded += r

    def encode_fixed(self, data_asterix, datafield):
        length = int(datafield.getAttribute('length'))
        bitslist = datafield.getElementsByTagName('Bits')

        encoded_bytes = 0
        encoded_num = 0         # the num of encoded asterix sub filed
        for bits in bitslist:
            bit_name = bits.getElementsByTagName('BitsShortName')[
                0].firstChild.nodeValue

            if bit_name in data_asterix:
                # skip spare,FX and zero subfield
                if bit_name in ['FX', 'spare'] or data_asterix[bit_name] == 0:
                    del data_asterix[bit_name]
                    continue

                encoded_num += 1
                bit = bits.getAttribute('bit')
                if bit != '':
                    _shift = int(bit) - 1
                    encoded_bytes |= (1 << _shift)
                else:
                    _from = int(bits.getAttribute('from'))
                    _to = int(bits.getAttribute('to'))

                    if _from < _to:  # swap values
                        _from, _to = _to, _from

                    v = data_asterix[bit_name]

                    BitsUnit = bits.getElementsByTagName("BitsUnit")
                    if BitsUnit:
                        scale = BitsUnit[0].getAttribute('scale')
                        v = int(v / float(scale))

                    # signed to unsigned, just & 0b11111...
                    mask = (1 << (_from - _to + 1)) - 1    # 0b1111111....
                    v &= mask
                    v <<= (_to - 1)

                    encoded_bytes |= v
                del data_asterix[bit_name]

        return encoded_num, (encoded_bytes).to_bytes(length, 'big')

    def encode_variable(self, data_asterix, datafield):
        result = bytearray()
        encoded_num = 0

        for fixed in datafield.getElementsByTagName('Fixed'):
            n, r = self.encode_fixed(data_asterix, fixed)
            encoded_num += n
            result += r

            if data_asterix:
                result[-1] |= 1   # set FX=1
            else:
                break

        return encoded_num, result

    # still not validated, may be wrong :)
    def encode_repetitive(self, data_asterix, datafield):
        assert type(data_asterix) is list
        result = bytearray()

        length = len(data_asterix)
        result += bytes([length])   # one byte length
        encoded_num = 0

        # repetive has only one subfiled, Fixed
        fixed = datafield.getElementsByTagName('Fixed')[0]
        for subdata in data_asterix:
            n, r = self.encode_fixed(subdata, fixed)
            encoded_num += n
            result += r

        return encoded_num, result

    def encode_compound(self, data_asterix, datafield):
        result = bytearray()
        encoded_num = 0

        index = 0
        indexs = []
        for cn in datafield.childNodes:
            if cn.nodeName not in ['Fixed', 'Repetitive', 'Variable', 'Compound']:
                continue

            index += 1      # current node index

            if index == 1:      # skip first node, it's indicator
                continue

            if index % 8 == 0:  # Fx field
                index += 1

            if cn.nodeName == 'Fixed':
                n, r = self.encode_fixed(data_asterix, cn)
            elif cn.nodeName == 'Repetitive':
                n, r = self.encode_repetitive(data_asterix, cn)
            elif cn.nodeName == 'Variable':
                n, r = self.decode_variable(data_asterix, cn)
            elif cn.nodeName == 'Compound':
                n, r = self.decode_compound(data_asterix, cn)

            if n == 0:
                continue
            encoded_num += n
            result += r
            indexs.append(index)

        indicator = 0
        maxindex = indexs[-1]
        indicator_bytes = (maxindex + 7) // 8   # how many indicator bytes

        # set indicator bits
        for index in indexs:
            _shift = indicator_bytes * 8 - index
            indicator |= (1 << _shift)

        # set Fx bits
        for i in range(1, indicator_bytes):  # lasst Fx is zero
            _shift = i * 8
            indicator |= (1 << _shift)

        result = (indicator).to_bytes(indicator_bytes, 'big') + result
        return encoded_num, result


class AsterixDecoder():
    # cat is asterix category, bytesdata is the bytes data to decode
    def __init__(self, bytesdata):
        self.bytes = bytesdata
        self.length = 0
        self.p = 0           # current decode postion

        self.decoded_result = {}

        # ------------------ cat -------------------------------
        cat = int.from_bytes(self.bytes[0:1], byteorder='big', signed=True)
        self.p += 1

        try:
            self.cat = minidom.parse(filenames[cat])
            category = self.cat.getElementsByTagName('Category')[0]
            self.dataitems = category.getElementsByTagName('DataItem')
            uap = category.getElementsByTagName('UAP')[0]
            self.uapitems = uap.getElementsByTagName('UAPItem')
        except:
            print('cat %d not supported now' % cat)
            return

        self.decoded_result[cat] = []

        # ------------------ length -------------------------------
        self.length = int.from_bytes(
            self.bytes[self.p:self.p + 2], byteorder='big', signed=True)
        self.p += 2

        while self.p < self.length:
            self.decoded = {}
            self.decode()
            self.decoded_result[cat].append(self.decoded)

    def get_result(self):
        return self.decoded_result

    def decode(self):
        # ------------------ FSPEC -------------------------------
        fspec_octets = 0
        fspec_octets_len = 0
        while True:
            _b = self.bytes[self.p]
            self.p += 1
            fspec_octets = (fspec_octets << 8) + _b
            fspec_octets_len += 1
            if _b & 1 == 0:
                break

        # ------------------ FSPEC bits to uapitem id --------------------------
        itemids = []  # dataitems
        # mask is 0b1000000000...
        mask = 1 << (8 * fspec_octets_len - 1)

        for i in range(0, 8 * fspec_octets_len):
            if fspec_octets & mask > 0:
                itemid = self.uapitems[i].firstChild.nodeValue
                if itemid != '-':
                    itemids.append(itemid)

            mask >>= 1

        # ------------------ decode each dataitem --------------------------
        for itemid in itemids:
            for dataitem in self.dataitems:
                if dataitem.getAttribute('id') == itemid:
                    dataitemformat = dataitem.getElementsByTagName('DataItemFormat')[
                        0]
                    for cn in dataitemformat.childNodes:
                        r = None
                        if cn.nodeName == 'Fixed':
                            r = self.decode_fixed(cn)
                        elif cn.nodeName == 'Repetitive':
                            r = self.decode_repetitive(cn)
                        elif cn.nodeName == 'Variable':
                            r = self.decode_variable(cn)
                        elif cn.nodeName == 'Compound':
                            r = self.decode_compound(cn)

                        if r:
                            self.decoded.update({itemid: r})

    def decode_fixed(self, datafield):
        results = {}
        length = int(datafield.getAttribute('length'))
        bitslist = datafield.getElementsByTagName('Bits')

        _bytes = self.bytes[self.p: self.p + length]
        self.p += length

        data = int.from_bytes(_bytes, byteorder='big', signed=False)

        for bits in bitslist:
            bit_name = bits.getElementsByTagName('BitsShortName')[
                0].firstChild.nodeValue

            bit = bits.getAttribute('bit')
            if bit != '':
                bit = int(bit)
                results[bit_name] = ((data >> (bit - 1)) & 1)

            else:
                from_ = int(bits.getAttribute('from'))
                to_ = int(bits.getAttribute('to'))

                if from_ < to_:  # swap values
                    from_, to_ = to_, from_
                mask = (1 << (from_ - to_ + 1)) - 1
                results[bit_name] = ((data >> (to_ - 1)) & mask)

                if bits.getAttribute('encode') == 'signed':
                    if results[bit_name] & (1 << (from_ - to_)):       # signed val
                        results[bit_name] = - \
                            (1 << (from_ - to_ + 1)) + results[bit_name]

                BitsUnit = bits.getElementsByTagName("BitsUnit")
                if BitsUnit:
                    scale = BitsUnit[0].getAttribute('scale')
                    results[bit_name] = results[bit_name] * float(scale)

        return results

    def decode_variable(self, datafield):
        results = {}

        for fixed in datafield.getElementsByTagName('Fixed'):
            r = self.decode_fixed(fixed)
            results.update(r)
            assert 'FX' in r
            if r['FX'] == 0:
                break

        return results

    def decode_repetitive(self, datafield):
        rep = self.bytes[self.p]
        self.p += 1

        results = []
        fixed = datafield.getElementsByTagName('Fixed')[0]
        for i in range(rep):
            r = self.decode_fixed(fixed)
            results.append(r)

        return results

    def decode_compound(self, datafield):
        # first variable field is indicators of all the subfields
        # all subfield indicators
        # --------------------------get indicators-------------
        indicator_octets = 0
        indicator_octetslen = 0
        while True:
            _b = self.bytes[self.p]
            self.p += 1
            indicator_octets = (indicator_octets << 8) + _b
            indicator_octetslen += 1

            if _b & 1 == 0:  # FX is zero
                break

        indicators = []
        mask = 1 << (8 * indicator_octetslen - 1)
        indicator = 1
        for i in range(0, 8 * indicator_octetslen):
            if i % 8 != 7:  # i is FX
                continue

            if indicator_octets & (mask >> i) > 0:
                indicators.append(indicator)

            indicator += 1

        # --------------------decode data------------------------
        results = {}
        index = 0
        for cn in datafield.childNodes:
            if cn.nodeName not in ['Fixed', 'Repetitive', 'Variable', 'Compound']:
                continue

            if index not in indicator:
                index += 1
                continue

            if cn.nodeName == 'Fixed':
                r = self.decode_fixed(cn)
            elif cn.nodeName == 'Repetitive':
                r = self.decode_repetitive(cn)
            elif cn.nodeName == 'Variable':
                r = self.decode_variable(cn)
            elif cn.nodeName == 'Compound':
                r = self.decode_compound(cn)

            index += 1
            results.update(r)

        return results


if __name__ == '__main__':

    def bytes2hexstr(_bytes):
        return "".join("%02X" % b for b in _bytes)

    hexstr = '15004EFF9FB35B83E40001080001014CFBA315CD2A4A0EAF0AE69555250757D74CFB330005554CFBA31189374B4CFB3319CAC08341C60A00500C000000F500004CFBB3414175D75820006A06D901'
    ad = AsterixDecoder(bytearray.fromhex(hexstr))
    print('decode result:', type(ad.get_result()), ad.get_result())

    ae = AsterixEncoder(ad.get_result())
    hexstr2 = bytes2hexstr(ae.get_result())
    print(hexstr2)
    assert(hexstr == hexstr2)

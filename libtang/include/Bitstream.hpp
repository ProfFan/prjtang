#ifndef LIBTANG_BITSTREAM_HPP
#define LIBTANG_BITSTREAM_HPP

#include <cstdint>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace Tang {

class Crc16
{
    static const uint16_t CRC16_POLY = 0x8005;
    static const uint16_t CRC16_INIT = 0x0000;
    uint16_t crc16 = CRC16_INIT;

  public:
    void update_crc16(uint8_t val);
    uint16_t finalise_crc16();
    void reset_crc16(uint16_t init = 0x0000);
    uint16_t calc(const std::vector<uint8_t> &data, int start, int end);
    uint16_t update_block(const std::vector<uint8_t> &data, int start, int end);
};

class Bitstream
{
  public:
    static Bitstream read(std::istream &in);

    void parse();
    void parse_block(const std::vector<uint8_t> &data);
    void parse_command(const uint8_t command, const uint16_t size, const std::vector<uint8_t> &data,
                       const uint16_t crc16);
    void parse_command_cpld(const uint8_t command, const uint16_t size, const std::vector<uint8_t> &data,
                            const uint16_t crc16);
    uint16_t calculate_bitstream_crc();

  private:
    Bitstream(const std::vector<uint8_t> &data, const std::vector<std::string> &metadata);

    std::string vector_to_string(const std::vector<uint8_t> &data);

    uint16_t data_blocks;
    // Raw bitstream data
    std::vector<uint8_t> data;
    // BIT file metadata
    std::vector<std::string> metadata;
    // status if bitstream is from CPLD
    bool cpld;

    uint16_t rows;
    uint16_t row_bytes;

    Crc16 crc;
};

class BitstreamParseError : std::runtime_error
{
  public:
    explicit BitstreamParseError(const std::string &desc);

    BitstreamParseError(const std::string &desc, size_t offset);

    const char *what() const noexcept override;

  private:
    std::string desc;
    int offset;
};
}
#endif // LIBTANG_BITSTREAM_HPP
